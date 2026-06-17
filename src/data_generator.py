import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# مسیر پایه پروژه — مهم نیست از کجا ران بشه
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DIR = os.path.join(BASE_DIR, 'data', 'sample')
os.makedirs(SAMPLE_DIR, exist_ok=True)

# ============================================================
# DATA GENERATOR — RzKala (فروشگاه آنلاین آرایشی و بهداشتی)
# نسخه ۲ — ad_spend ساده با campaign
# ============================================================

np.random.seed(42)
random.seed(42)

# بازه زمانی: ۳ ماه (پاییز ۱۴۰۲)
start_date = datetime(2023, 9, 23)  # ۱ مهر ۱۴۰۲
end_date = datetime(2023, 12, 21)   # ۳۰ آذر ۱۴۰۲
date_range = pd.date_range(start=start_date, end=end_date, freq='D')

# ============================================================
# ۱. محصولات
# ============================================================
products = {
    'کرم ضد آفتاب SPF50': {'category': 'مراقبت پوست', 'unit_cost': 180_000, 'unit_price': 320_000},
    'کرم مرطوب‌کننده روزانه': {'category': 'مراقبت پوست', 'unit_cost': 150_000, 'unit_price': 280_000},
    'سرم ویتامین C': {'category': 'مراقبت پوست', 'unit_cost': 220_000, 'unit_price': 450_000},
    'شوینده صورت ژله‌ای': {'category': 'مراقبت پوست', 'unit_cost': 120_000, 'unit_price': 200_000},
    'تونر گل رز': {'category': 'مراقبت پوست', 'unit_cost': 90_000, 'unit_price': 180_000},
    'رژ لب مات قرمز': {'category': 'آرایشی', 'unit_cost': 140_000, 'unit_price': 260_000},
    'رژ لب مایع nude': {'category': 'آرایشی', 'unit_cost': 130_000, 'unit_price': 240_000},
    'کرم پودر مات کننده': {'category': 'آرایشی', 'unit_cost': 200_000, 'unit_price': 380_000},
    'خط چشم ضد آب': {'category': 'آرایشی', 'unit_cost': 110_000, 'unit_price': 200_000},
    'پالت سایه ۱۲ رنگ': {'category': 'آرایشی', 'unit_cost': 250_000, 'unit_price': 500_000},
    'ریمل حجم‌دهنده': {'category': 'آرایشی', 'unit_cost': 100_000, 'unit_price': 190_000},
    'شامپو ترمیم‌کننده': {'category': 'مراقبت مو', 'unit_cost': 160_000, 'unit_price': 300_000},
    'ماسک مو روغن آرگان': {'category': 'مراقبت مو', 'unit_cost': 130_000, 'unit_price': 250_000},
    'اسپری حالت‌دهنده مو': {'category': 'مراقبت مو', 'unit_cost': 100_000, 'unit_price': 200_000},
    'روغن مو طبیعی': {'category': 'مراقبت مو', 'unit_cost': 90_000, 'unit_price': 180_000},
    'عطر مردانه ۵۰ میل': {'category': 'عطر و ادکلن', 'unit_cost': 350_000, 'unit_price': 650_000},
    'عطر زنانه ۳۰ میل': {'category': 'عطر و ادکلن', 'unit_cost': 400_000, 'unit_price': 750_000},
    'ادکلن اسپرت ۱۰۰ میل': {'category': 'عطر و ادکلن', 'unit_cost': 280_000, 'unit_price': 550_000},
}

# ============================================================
# ۲. کمپین‌ها (مستقل از کانال — فقط اسم کمپین)
# ============================================================
campaigns = [
    'g_brand',           # گوگل — جستجوی برند
    'g_generic',         # گوگل — جستجوی عمومی
    'ig_influencer',     # اینستاگرام — اینفلوئنسر
    'ig_story_ads',      # اینستاگرام — استوری تبلیغاتی
    'email_newsletter',  # ایمیل — خبرنامه
]

device_types = ['mobile', 'desktop', 'tablet']
device_weights = [0.70, 0.25, 0.05]

# ============================================================
# ۳. تولید سفارشات (orders) — ستون utm_campaign داره
# ============================================================
orders_rows = []
order_id_counter = 1000

customers = [f'09{random.randint(100000000, 999999999)}' for _ in range(500)]

for single_date in date_range:
    day_of_week = single_date.weekday()
    daily_order_count = int(np.random.normal(40, 10) * (1.3 if day_of_week >= 5 else 1.0))
    daily_order_count = max(5, daily_order_count)

    for _ in range(daily_order_count):
        hour_weights = [0.02]*6 + [0.08]*4 + [0.04]*4 + [0.10]*4 + [0.12]*4 + [0.04]*2
        hour = random.choices(range(24), weights=hour_weights)[0]
        minute = random.randint(0, 59)
        order_datetime = single_date + timedelta(hours=hour, minutes=minute)

        campaign = random.choice(campaigns)
        device = random.choices(device_types, weights=device_weights)[0]

        order_status = random.choices(
            ['completed', 'cancelled', 'refunded'],
            weights=[0.85, 0.10, 0.05]
        )[0]

        phone = random.choice(customers)

        num_products = random.choices([1, 2, 3, 4], weights=[0.60, 0.25, 0.10, 0.05])[0]
        selected_products = random.sample(list(products.keys()), min(num_products, len(products)))

        for product_name in selected_products:
            product_info = products[product_name]
            quantity = random.choices([1, 2, 3], weights=[0.80, 0.15, 0.05])[0]

            discount_pct = 0
            if random.random() < 0.20:
                discount_pct = random.choice([0.10, 0.15, 0.20, 0.25, 0.30, 0.40])

            unit_price_original = product_info['unit_price']
            unit_price_discounted = int(unit_price_original * (1 - discount_pct))
            total_price = unit_price_discounted * quantity

            orders_rows.append({
                'order_id': order_id_counter,
                'order_datetime': order_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'order_date': order_datetime.strftime('%Y-%m-%d'),
                'order_hour': hour,
                'customer_phone': phone,
                'product_name': product_name,
                'category': product_info['category'],
                'quantity': quantity,
                'unit_price': unit_price_discounted,
                'unit_cost': product_info['unit_cost'],
                'total_price': total_price,
                'discount_pct': discount_pct,
                'device': device,
                'utm_campaign': campaign,
                'order_status': order_status,
            })

        order_id_counter += 1

orders_df = pd.DataFrame(orders_rows)

# ============================================================
# ۴. تولید ترافیک (traffic) — ستون utm_campaign داره
# ============================================================
traffic_rows = []

for single_date in date_range:
    day_of_week = single_date.weekday()
    traffic_multiplier = 1.5 if day_of_week >= 5 else (1.3 if day_of_week == 4 else 1.0)

    for campaign in campaigns:
        base_sessions = int(np.random.normal(120, 25) * traffic_multiplier)
        sessions = max(5, base_sessions)

        product_view_rate = np.random.normal(0.65, 0.08)
        add_to_cart_rate = np.random.normal(0.25, 0.05)
        checkout_rate = np.random.normal(0.55, 0.07)

        product_views = int(sessions * max(0.1, product_view_rate))
        add_to_cart = int(product_views * max(0.05, add_to_cart_rate))
        begin_checkout = int(add_to_cart * max(0.1, checkout_rate))

        traffic_rows.append({
            'date': single_date.strftime('%Y-%m-%d'),
            'utm_campaign': campaign,
            'sessions': sessions,
            'product_page_views': product_views,
            'add_to_cart': add_to_cart,
            'begin_checkout': begin_checkout,
        })

traffic_df = pd.DataFrame(traffic_rows)

# ============================================================
# ۵. تولید هزینه تبلیغات (ad_spend) — فقط date, campaign, spend
# ============================================================
campaign_daily_budget = {
    'g_brand': 1_500_000,
    'g_generic': 800_000,
    'ig_influencer': 1_200_000,
    'ig_story_ads': 1_000_000,
    'email_newsletter': 200_000,
}

ad_spend_rows = []

for single_date in date_range:
    for campaign, budget in campaign_daily_budget.items():
        actual_cost = int(np.random.normal(budget, budget * 0.15))
        actual_cost = max(50_000, actual_cost)

        ad_spend_rows.append({
            'date': single_date.strftime('%Y-%m-%d'),
            'campaign': campaign,
            'spend': actual_cost,
        })

ad_spend_df = pd.DataFrame(ad_spend_rows)

# ============================================================
# ۶. ذخیره
# ============================================================
orders_df.to_csv(os.path.join(SAMPLE_DIR, 'orders.csv'), index=False, encoding='utf-8-sig')
traffic_df.to_csv(os.path.join(SAMPLE_DIR, 'traffic.csv'), index=False, encoding='utf-8-sig')
ad_spend_df.to_csv(os.path.join(SAMPLE_DIR, 'ad_spend.csv'), index=False, encoding='utf-8-sig')

# ============================================================
# ۷. گزارش
# ============================================================
print("✅ نسخه ۲ با موفقیت ساخته شد!")
print(f"\n📦 orders.csv:")
print(f"   {len(orders_df):,} ردیف | {orders_df['order_id'].nunique():,} سفارش")
print(f"   ستون‌ها: {list(orders_df.columns)}")
print(f"\n📊 traffic.csv:")
print(f"   {len(traffic_df):,} ردیف | {traffic_df['sessions'].sum():,} جلسه")
print(f"   ستون‌ها: {list(traffic_df.columns)}")
print(f"\n💰 ad_spend.csv:")
print(f"   {len(ad_spend_df):,} ردیف | {ad_spend_df['spend'].sum():,} ریال")
print(f"   ستون‌ها: {list(ad_spend_df.columns)}")

# نمایش ۳ خط اول هر فایل
print("\n--- orders.csv (first 3) ---")
print(orders_df.head(3).to_string())
print("\n--- traffic.csv (first 3) ---")
print(traffic_df.head(3).to_string())
print("\n--- ad_spend.csv (first 3) ---")
print(ad_spend_df.head(3).to_string())


#test db really exist
import pandas as pd
df = pd.read_csv('data/sample/ad_spend.csv')
print(df.shape)
print(df.columns.tolist())
print(df.head(3))