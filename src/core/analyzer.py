import duckdb
import pandas as pd
import os

# ============================================================
# ANALYZER — Flexible SQL analysis engine
# Auto-detects available columns, skips what's missing
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DIR = os.path.join(BASE_DIR, 'data', 'sample')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')


def apply_filters(orders_df, traffic_df=None, ad_spend_df=None,
                  date_from=None, date_to=None,
                  utm_sources=None, campaigns=None,
                  order_status=None):
    orders_f = orders_df.copy()
    traffic_f = traffic_df.copy() if traffic_df is not None else None
    ad_spend_f = ad_spend_df.copy() if ad_spend_df is not None else None

    has_date = 'order_date' in orders_f.columns
    if date_from and has_date:
        orders_f = orders_f[orders_f['order_date'] >= date_from]
        if traffic_f is not None and 'date' in traffic_f.columns:
            traffic_f = traffic_f[traffic_f['date'] >= date_from]
        if ad_spend_f is not None and 'date' in ad_spend_f.columns:
            ad_spend_f = ad_spend_f[ad_spend_f['date'] >= date_from]

    if date_to and has_date:
        orders_f = orders_f[orders_f['order_date'] <= date_to]
        if traffic_f is not None and 'date' in traffic_f.columns:
            traffic_f = traffic_f[traffic_f['date'] <= date_to]
        if ad_spend_f is not None and 'date' in ad_spend_f.columns:
            ad_spend_f = ad_spend_f[ad_spend_f['date'] <= date_to]

    if campaigns and 'utm_campaign' in orders_f.columns:
        orders_f = orders_f[orders_f['utm_campaign'].isin(campaigns)]
        if traffic_f is not None and 'utm_campaign' in traffic_f.columns:
            traffic_f = traffic_f[traffic_f['utm_campaign'].isin(campaigns)]
        if ad_spend_f is not None and 'campaign' in ad_spend_f.columns:
            ad_spend_f = ad_spend_f[ad_spend_f['campaign'].isin(campaigns)]

    if utm_sources and 'utm_source' in orders_f.columns:
        orders_f = orders_f[orders_f['utm_source'].isin(utm_sources)]

    if order_status and 'order_status' in orders_f.columns:
        orders_f = orders_f[orders_f['order_status'].isin(order_status)]

    return {'orders': orders_f, 'traffic': traffic_f, 'ad_spend': ad_spend_f}


def run_all_analyses(orders_df, traffic_df=None, ad_spend_df=None):
    """Run all possible analyses based on available columns. Skips what's missing."""

    available = {
        'order_date': 'order_date' in orders_df.columns,
        'customer_phone': 'customer_phone' in orders_df.columns,
        'order_id': 'order_id' in orders_df.columns,
        'total_price': 'total_price' in orders_df.columns,
        'unit_cost': 'unit_cost' in orders_df.columns,
        'quantity': 'quantity' in orders_df.columns,
        'product_name': 'product_name' in orders_df.columns,
        'order_status': 'order_status' in orders_df.columns,
        'category': 'category' in orders_df.columns,
        'discount_pct': 'discount_pct' in orders_df.columns,
        'utm_campaign': 'utm_campaign' in orders_df.columns,
    }

    conn = duckdb.connect(':memory:')
    conn.register('orders', orders_df)

    has_traffic = traffic_df is not None and len(traffic_df) > 0
    has_ad_spend = ad_spend_df is not None and len(ad_spend_df) > 0

    if has_traffic:
        conn.register('traffic', traffic_df)
    if has_ad_spend:
        conn.register('ad_spend', ad_spend_df)

    status_filter = "WHERE order_status = 'completed'" if available['order_status'] else ""
    profit_expr = "(total_price - (unit_cost * quantity))" if available['unit_cost'] and available['quantity'] else "total_price"

    results = {}
    log = []

    # 1. KPI
    if available['total_price'] and available['order_id']:
        kpi_query = f"""
            SELECT
                COUNT(DISTINCT order_id) AS total_orders,
                SUM(total_price) AS total_revenue,
                SUM({profit_expr}) AS total_profit,
                ROUND(AVG(total_price), 0) AS avg_order_value,
                ROUND(SUM(total_price) * 1.0 / NULLIF(COUNT(DISTINCT order_id), 0), 0) AS revenue_per_order,
                COUNT(DISTINCT customer_phone) AS unique_customers
            FROM orders
            {status_filter}
        """ if available['customer_phone'] else f"""
            SELECT
                COUNT(DISTINCT order_id) AS total_orders,
                SUM(total_price) AS total_revenue,
                SUM({profit_expr}) AS total_profit,
                ROUND(AVG(total_price), 0) AS avg_order_value,
                ROUND(SUM(total_price) * 1.0 / NULLIF(COUNT(DISTINCT order_id), 0), 0) AS revenue_per_order,
                0 AS unique_customers
            FROM orders
            {status_filter}
        """
        results['kpi'] = conn.execute(kpi_query).fetchdf()
        log.append("KPI: calculated")
    else:
        log.append("KPI: skipped (needs total_price + order_id)")

    # 2. Funnel
    if has_traffic and available['order_id']:
        purchases = conn.execute(f"SELECT COUNT(DISTINCT order_id) FROM orders {status_filter}").fetchone()[0]
        funnel_query = f"""
            SELECT 'Sessions' AS stage, SUM(sessions) AS count FROM traffic
            UNION ALL SELECT 'Product Views', SUM(product_page_views) FROM traffic
            UNION ALL SELECT 'Add to Cart', SUM(add_to_cart) FROM traffic
            UNION ALL SELECT 'Begin Checkout', SUM(begin_checkout) FROM traffic
            UNION ALL SELECT 'Purchases', {purchases}
            ORDER BY count DESC
        """
        results['funnel'] = conn.execute(funnel_query).fetchdf()
        log.append("Funnel: calculated")
    else:
        log.append("Funnel: skipped (needs traffic data)")

    # 3. ROAS
    if has_traffic and has_ad_spend and available['utm_campaign'] and available['total_price']:
        roas_query = f"""
            WITH campaign_revenue AS (
                SELECT utm_campaign, SUM(total_price) AS revenue, COUNT(DISTINCT order_id) AS purchases
                FROM orders {status_filter}
                GROUP BY utm_campaign
            ),
            campaign_cost AS (
                SELECT campaign, SUM(spend) AS total_spend FROM ad_spend GROUP BY campaign
            )
            SELECT
                COALESCE(cr.utm_campaign, cc.campaign) AS campaign,
                COALESCE(cr.revenue, 0) AS revenue,
                COALESCE(cc.total_spend, 0) AS spend,
                COALESCE(cr.purchases, 0) AS purchases,
                CASE WHEN cc.total_spend > 0 THEN ROUND(cr.revenue * 1.0 / cc.total_spend, 2) END AS roas
            FROM campaign_revenue cr
            FULL OUTER JOIN campaign_cost cc ON cr.utm_campaign = cc.campaign
            ORDER BY roas DESC
        """
        results['roas'] = conn.execute(roas_query).fetchdf()
        log.append("ROAS: calculated")
    else:
        log.append("ROAS: skipped (needs traffic + ad_spend + campaign)")

    # 4. RFM
    if available['customer_phone'] and available['order_id'] and available['total_price']:
        if available['order_date']:
            max_date = conn.execute("SELECT MAX(CAST(order_date AS DATE)) FROM orders").fetchone()[0]
            rfm_query = f"""
                WITH rfm_raw AS (
                    SELECT customer_phone,
                        DATEDIFF('day', CAST(MAX(order_date) AS DATE), DATE '{max_date}') AS recency,
                        COUNT(DISTINCT order_id) AS frequency, SUM(total_price) AS monetary
                    FROM orders {status_filter} GROUP BY customer_phone
                ),
                rfm_scored AS (
                    SELECT *, NTILE(5) OVER (ORDER BY recency ASC) AS r_score,
                        NTILE(5) OVER (ORDER BY frequency DESC) AS f_score,
                        NTILE(5) OVER (ORDER BY monetary DESC) AS m_score
                    FROM rfm_raw
                ),
                rfm_segments AS (
                    SELECT *, (r_score + f_score + m_score) AS rfm_total,
                        CASE
                            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'VIP'
                            WHEN r_score >= 4 AND f_score < 3 THEN 'New'
                            WHEN r_score < 3 AND f_score >= 4 THEN 'At Risk'
                            WHEN r_score < 2 AND f_score < 2 THEN 'Lost'
                            WHEN r_score >= 3 AND f_score >= 2 THEN 'Active'
                            ELSE 'Regular' END AS segment
                    FROM rfm_scored
                )
                SELECT segment, COUNT(*) AS customer_count, ROUND(AVG(monetary),0) AS avg_value, SUM(monetary) AS total_value
                FROM rfm_segments GROUP BY segment ORDER BY total_value DESC
            """
        else:
            rfm_query = f"""
                WITH rfm_raw AS (
                    SELECT customer_phone, COUNT(DISTINCT order_id) AS frequency, SUM(total_price) AS monetary
                    FROM orders {status_filter} GROUP BY customer_phone
                ),
                rfm_scored AS (
                    SELECT *, NTILE(5) OVER (ORDER BY frequency DESC) AS f_score,
                        NTILE(5) OVER (ORDER BY monetary DESC) AS m_score
                    FROM rfm_raw
                ),
                rfm_segments AS (
                    SELECT *, (f_score + m_score) AS rfm_total,
                        CASE
                            WHEN f_score >= 4 AND m_score >= 4 THEN 'VIP'
                            WHEN f_score < 3 AND m_score >= 4 THEN 'At Risk'
                            WHEN f_score < 2 AND m_score < 2 THEN 'Lost'
                            WHEN f_score >= 3 AND m_score >= 2 THEN 'Active'
                            ELSE 'Regular' END AS segment
                    FROM rfm_scored
                )
                SELECT segment, COUNT(*) AS customer_count, ROUND(AVG(monetary),0) AS avg_value, SUM(monetary) AS total_value
                FROM rfm_segments GROUP BY segment ORDER BY total_value DESC
            """
        results['rfm'] = conn.execute(rfm_query).fetchdf()
        log.append("RFM: calculated")
    else:
        log.append("RFM: skipped (needs customer_phone + order_id + total_price)")

    # 5. Profitability
    if available['product_name'] and available['total_price']:
        cat_col = "category" if available['category'] else None
        cat_select = "category, " if cat_col else ""
        cat_group = "category, " if cat_col else ""
        profitability_query = f"""
            WITH product_profit AS (
                SELECT {cat_select}product_name,
                    SUM(quantity) AS total_qty, SUM(total_price) AS revenue,
                    SUM({profit_expr}) AS profit, COUNT(DISTINCT order_id) AS order_count
                FROM orders {status_filter}
                GROUP BY {cat_group}product_name
            )
            SELECT *, ROUND(profit * 100.0 / SUM(profit) OVER (), 1) AS profit_pct,
                ROUND(SUM(profit) OVER (ORDER BY profit DESC) * 100.0 / SUM(profit) OVER (), 1) AS cumulative_profit_pct
            FROM product_profit ORDER BY profit DESC
        """
        results['profitability'] = conn.execute(profitability_query).fetchdf()
        log.append("Profitability: calculated")
    else:
        log.append("Profitability: skipped (needs product_name + total_price)")

    # 6. Trend
    if available['order_date'] and available['total_price']:
        trend_query = f"""
            SELECT order_date AS date, COUNT(DISTINCT order_id) AS orders,
                SUM(total_price) AS revenue, SUM({profit_expr}) AS profit
            FROM orders {status_filter}
            GROUP BY order_date ORDER BY order_date
        """
        results['trend'] = conn.execute(trend_query).fetchdf()

        trend_weekly_query = f"""
            SELECT DATE_TRUNC('week', CAST(order_date AS DATE)) AS week,
                COUNT(DISTINCT order_id) AS orders, SUM(total_price) AS revenue,
                SUM({profit_expr}) AS profit
            FROM orders {status_filter}
            GROUP BY week ORDER BY week
        """
        results['trend_weekly'] = conn.execute(trend_weekly_query).fetchdf()
        log.append("Trend: calculated")
    else:
        results['trend'] = pd.DataFrame()
        results['trend_weekly'] = pd.DataFrame()
        log.append("Trend: skipped (needs order_date)")

    # 7. Repeat Rate
    if available['customer_phone'] and available['order_id']:
        repeat_query = f"""
            WITH customer_orders AS (
                SELECT customer_phone, COUNT(DISTINCT order_id) AS order_count
                FROM orders {status_filter} GROUP BY customer_phone
            )
            SELECT CASE
                WHEN order_count = 1 THEN 'One-time'
                WHEN order_count = 2 THEN 'Twice'
                WHEN order_count BETWEEN 3 AND 5 THEN '3-5 times'
                ELSE '6+ times' END AS customer_type,
                COUNT(*) AS customer_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
            FROM customer_orders GROUP BY customer_type ORDER BY customer_count DESC
        """
        results['repeat_rate'] = conn.execute(repeat_query).fetchdf()
        log.append("Repeat Rate: calculated")
    else:
        log.append("Repeat Rate: skipped (needs customer_phone + order_id)")

    # 8. Scatter
    if available['product_name'] and available['total_price']:
        scatter_query = f"""
            SELECT product_name, SUM(total_price) AS total_revenue,
                SUM({profit_expr}) AS total_profit, COUNT(*) AS units_sold
            FROM orders {status_filter}
            GROUP BY product_name ORDER BY total_profit DESC
        """
        results['scatter_data'] = conn.execute(scatter_query).fetchdf()
        log.append("Scatter: calculated")

    # 9. TreeMap
    if available['product_name'] and available['total_price']:
        treemap_query = f"""
            SELECT product_name, SUM(total_price) AS revenue, COUNT(*) AS items_sold
            FROM orders {status_filter}
            GROUP BY product_name ORDER BY revenue DESC
        """
        results['treemap_data'] = conn.execute(treemap_query).fetchdf()
        log.append("TreeMap: calculated")

    # 10. Discount Impact
    if available['discount_pct'] and available['total_price']:
        discount_query = f"""
            SELECT CASE
                WHEN discount_pct = 0 THEN 'No Discount'
                WHEN discount_pct <= 0.10 THEN '1-10%'
                WHEN discount_pct <= 0.20 THEN '11-20%'
                WHEN discount_pct <= 0.30 THEN '21-30%'
                ELSE '30%+' END AS discount_range,
                COUNT(DISTINCT order_id) AS orders, SUM(total_price) AS revenue,
                SUM({profit_expr}) AS profit
            FROM orders {status_filter}
            GROUP BY discount_range ORDER BY profit DESC
        """
        results['discount_impact'] = conn.execute(discount_query).fetchdf()
        log.append("Discount Impact: calculated")

    conn.close()
    results['_log'] = log
    return results


def print_summary(results):
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)

    if '_log' in results:
        for l in results['_log']:
            print(f"  {l}")

    if 'kpi' in results and len(results['kpi']) > 0:
        kpi = results['kpi'].iloc[0]
        print(f"\nKPI:")
        print(f"   Revenue: {kpi.get('total_revenue', 0):,.0f} Rials")
        print(f"   Profit: {kpi.get('total_profit', 0):,.0f} Rials")
        print(f"   Orders: {kpi.get('total_orders', 0):,.0f}")
        print(f"   AOV: {kpi.get('avg_order_value', 0):,.0f} Rials")
        print(f"   Customers: {kpi.get('unique_customers', 0):,.0f}")


if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, 'src'))
    from mapper import load_and_map

    print("Testing analyzer.py ...\n")
    data = load_and_map()
    results = run_all_analyses(
        orders_df=data['orders'],
        traffic_df=data['traffic'],
        ad_spend_df=data['ad_spend']
    )
    print_summary(results)