import pandas as pd


def detect_losses(orders_df):
    """
    تشخیص محصولات زیان‌ده و کمپین‌های بی‌بازده

    Returns:
        dict: alerts (list of str), loss_products (DataFrame)
    """
    alerts = []
    loss_products = pd.DataFrame()

    if orders_df is None or len(orders_df) == 0:
        return {'alerts': [], 'loss_products': loss_products}

    # ۱. محصولاتی که زیر قیمت خرید فروش رفتن (ضرر مستقیم)
    if 'unit_price' in orders_df.columns and 'unit_cost' in orders_df.columns:
        loss_mask = orders_df['unit_price'] < orders_df['unit_cost']
        if loss_mask.any():
            loss_products = orders_df[loss_mask].groupby('product_name').agg(
                total_loss=('total_price', lambda x: (
                            x - (orders_df.loc[x.index, 'unit_cost'] * orders_df.loc[x.index, 'quantity'])).sum()),
                loss_orders=('order_id', 'nunique')
            ).reset_index()
            loss_products = loss_products[loss_products['total_loss'] < 0]
            loss_products['total_loss'] = loss_products['total_loss'].abs()

            if len(loss_products) > 0:
                total_loss = loss_products['total_loss'].sum()
                alerts.append(
                    f"⚠️ **{len(loss_products)} محصول** زیر قیمت خرید فروش رفتن! ضرر کل: **{total_loss:,.0f} ریال**")

    # ۲. محصولات با تخفیف سنگین (>30%) که تعدادشون زیاده
    if 'discount_pct' in orders_df.columns:
        heavy_discount = orders_df[orders_df['discount_pct'] > 0.30]
        if len(heavy_discount) > 0:
            hd_count = heavy_discount['product_name'].nunique()
            alerts.append(f"🔻 **{hd_count} محصول** با تخفیف بالای ۳۰٪ فروش رفتن. حاشیه سود رو چک کن.")

    # ۳. نرخ لغوی/مرجوعی بالا
    if 'order_status' in orders_df.columns:
        total = len(orders_df)
        cancelled = len(orders_df[orders_df['order_status'].isin(['cancelled', 'refunded'])])
        if total > 0:
            cancel_rate = cancelled / total
            if cancel_rate > 0.15:
                alerts.append(f"🚫 نرخ لغو/مرجوعی **{cancel_rate:.1%}** هست! (بالای ۱۵٪). قیف پرداخت رو بررسی کن.")

    return {
        'alerts': alerts,
        'loss_products': loss_products
    }