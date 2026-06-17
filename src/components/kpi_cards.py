import pandas as pd


# ============================================================
# KPI CARDS — محاسبه و نمایش شاخص‌های کلیدی عملکرد
# (نسخه منعطف — با ستون‌های اختیاری)
# ============================================================

def get_kpi_cards(orders_df):
    """
    محاسبه KPIهای اصلی
    ستون‌های اجباری: total_price
    ستون‌های اختیاری: order_id, order_status, customer_phone, unit_cost, quantity
    """

    has_order_id = 'order_id' in orders_df.columns
    has_status = 'order_status' in orders_df.columns
    has_customer = 'customer_phone' in orders_df.columns
    has_cost = 'unit_cost' in orders_df.columns
    has_qty = 'quantity' in orders_df.columns

    # --- فیلتر completed ---
    if has_status:
        completed = orders_df[orders_df['order_status'] == 'completed'].copy()
        cancelled = orders_df[orders_df['order_status'] == 'cancelled']
    else:
        completed = orders_df.copy()
        cancelled = pd.DataFrame()

    # --- فروش کل ---
    total_revenue = completed['total_price'].sum() if 'total_price' in completed.columns else 0

    # --- سود ---
    if has_cost and has_qty:
        total_profit = (completed['total_price'] - (completed['unit_cost'] * completed['quantity'])).sum()
    else:
        total_profit = 0

    # --- تعداد سفارش ---
    if has_order_id:
        total_orders = completed['order_id'].nunique()
        all_orders = orders_df['order_id'].nunique() if has_order_id else total_orders
    else:
        total_orders = len(completed)
        all_orders = len(orders_df)

    # --- مشتریان یکتا ---
    if has_customer:
        unique_customers = completed['customer_phone'].nunique()
    elif has_order_id:
        unique_customers = total_orders
    else:
        unique_customers = len(completed)

    # --- AOV ---
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    # --- حاشیه سود ---
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

    # --- نرخ لغوی ---
    if has_status and has_order_id:
        cancelled_count = cancelled['order_id'].nunique() if len(cancelled) > 0 else 0
        cancellation_rate = (cancelled_count / all_orders * 100) if all_orders > 0 else 0
    else:
        cancellation_rate = 0

    return {
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'total_orders': total_orders,
        'unique_customers': unique_customers,
        'avg_order_value': avg_order_value,
        'profit_margin_pct': round(profit_margin, 1),
        'cancellation_rate': round(cancellation_rate, 1),
    }


def print_kpi_cards(kpi):
    """چاپ KPIها در ترمینال"""
    print("\n" + "=" * 50)
    print("📊 KPI CARDS")
    print("=" * 50)
    print(f"💰 فروش کل:        {kpi['total_revenue']:>15,.0f} ریال")
    print(f"📈 سود خالص:        {kpi['total_profit']:>15,.0f} ریال")
    print(f"📦 تعداد سفارش:     {kpi['total_orders']:>15,}")
    print(f"👥 مشتریان یکتا:    {kpi['unique_customers']:>15,}")
    print(f"🛒 میانگین سبد خرید: {kpi['avg_order_value']:>15,.0f} ریال")
    print(f"💎 حاشیه سود:       {kpi['profit_margin_pct']:>15}%")
    print(f"❌ نرخ لغوی:        {kpi['cancellation_rate']:>15}%")


if __name__ == '__main__':
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from mapper import load_and_map

    print("🧪 تست kpi_cards.py ...\n")
    data = load_and_map()
    kpi = get_kpi_cards(data['orders'])
    print_kpi_cards(kpi)