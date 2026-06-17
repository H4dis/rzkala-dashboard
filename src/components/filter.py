# src/components/filters.py

def apply_filters(orders_df, traffic_df=None, ad_spend_df=None,
                  date_from=None, date_to=None,
                  campaigns=None, utm_sources=None,
                  order_status=None):
    """
    اعمال فیلترهای زنجیره‌ای روی دیتا
    """

    orders_f = orders_df.copy()
    traffic_f = traffic_df.copy() if traffic_df is not None else None
    ad_spend_f = ad_spend_df.copy() if ad_spend_df is not None else None

    if date_from:
        orders_f = orders_f[orders_f['order_date'] >= date_from]
        if traffic_f is not None:
            traffic_f = traffic_f[traffic_f['date'] >= date_from]
        if ad_spend_f is not None:
            ad_spend_f = ad_spend_f[ad_spend_f['date'] >= date_from]

    if date_to:
        orders_f = orders_f[orders_f['order_date'] <= date_to]
        if traffic_f is not None:
            traffic_f = traffic_f[traffic_f['date'] <= date_to]
        if ad_spend_f is not None:
            ad_spend_f = ad_spend_f[ad_spend_f['date'] <= date_to]

    if campaigns:
        orders_f = orders_f[orders_f['utm_campaign'].isin(campaigns)]
        if traffic_f is not None:
            traffic_f = traffic_f[traffic_f['utm_campaign'].isin(campaigns)]
        if ad_spend_f is not None:
            ad_spend_f = ad_spend_f[ad_spend_f['campaign'].isin(campaigns)]

    if utm_sources and 'utm_source' in orders_f.columns:
        orders_f = orders_f[orders_f['utm_source'].isin(utm_sources)]

    if order_status:
        orders_f = orders_f[orders_f['order_status'].isin(order_status)]

    return {
        'orders': orders_f,
        'traffic': traffic_f,
        'ad_spend': ad_spend_f,
    }