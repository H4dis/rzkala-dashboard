import pandas as pd

# ============================================================
# FUNNEL CHART — محاسبه و تحلیل قیف فروش
# ============================================================

def get_funnel_data(orders_df, traffic_df=None):
    """
    محاسبه داده‌های قیف فروش
    """

    has_status = 'order_status' in orders_df.columns
    has_order_id = 'order_id' in orders_df.columns

    if traffic_df is None or len(traffic_df) == 0:
        # فقط آمار سفارشات
        if has_status:
            total_completed = orders_df[orders_df['order_status'] == 'completed']['order_id'].nunique() if has_order_id else len(orders_df[orders_df['order_status'] == 'completed'])
            total_cancelled = orders_df[orders_df['order_status'] == 'cancelled']['order_id'].nunique() if has_order_id else len(orders_df[orders_df['order_status'] == 'cancelled'])
            total_refunded = orders_df[orders_df['order_status'] == 'refunded']['order_id'].nunique() if has_order_id else len(orders_df[orders_df['order_status'] == 'refunded'])
        else:
            total_completed = orders_df['order_id'].nunique() if has_order_id else len(orders_df)
            total_cancelled = 0
            total_refunded = 0

        return pd.DataFrame([
            {'stage': 'سفارشات تکمیل', 'count': total_completed},
            {'stage': 'سفارشات لغو', 'count': total_cancelled},
            {'stage': 'سفارشات مرجوع', 'count': total_refunded},
        ])

    # با داده ترافیک — قیف کامل
    sessions = traffic_df['sessions'].sum()
    product_views = traffic_df['product_page_views'].sum()
    add_to_cart = traffic_df['add_to_cart'].sum()
    begin_checkout = traffic_df['begin_checkout'].sum()
    purchases = orders_df['order_id'].nunique() if has_order_id else len(orders_df)

    funnel = pd.DataFrame([
        {'stage': 'بازدید (Sessions)', 'count': int(sessions)},
        {'stage': 'مشاهده محصول', 'count': int(product_views)},
        {'stage': 'افزودن به سبد', 'count': int(add_to_cart)},
        {'stage': 'شروع تسویه', 'count': int(begin_checkout)},
        {'stage': 'خرید نهایی', 'count': int(purchases)},
    ])

    conversions = []
    for i in range(len(funnel)):
        if i == 0:
            conversions.append(100.0)
        else:
            prev = funnel.iloc[i-1]['count']
            curr = funnel.iloc[i]['count']
            conversions.append(round(curr / prev * 100, 1) if prev > 0 else 0)

    funnel['conversion_pct'] = conversions

    return funnel


def print_funnel(funnel_df):
    """چاپ قیف فروش در ترمینال"""
    print("\n" + "=" * 50)
    print("📈 FUNNEL ANALYSIS")
    print("=" * 50)

    for i, row in funnel_df.iterrows():
        bar = "█" * int(row['count'] / max(funnel_df['count'].max(), 1) * 30)
        print(f"{row['stage']:20s} | {row['count']:>10,.0f} | {bar}")
        if i > 0 and 'conversion_pct' in funnel_df.columns:
            print(f"{'':20s} | {'↳ نرخ تبدیل: ' + str(row['conversion_pct']) + '%':>10s}")

    if len(funnel_df) >= 2:
        first = funnel_df.iloc[0]['count']
        last = funnel_df.iloc[-1]['count']
        overall = round(last / first * 100, 1) if first > 0 else 0
        print(f"\n🎯 نرخ تبدیل کلی: {overall}%")


if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from mapper import load_and_map

    print("🧪 تست funnel_chart.py ...\n")
    data = load_and_map()
    funnel = get_funnel_data(data['orders'], data['traffic'])
    print_funnel(funnel)