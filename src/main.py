"""
RzKala — موتور تحلیل فروش
نقطه ورود اصلی
"""

import os
import sys

# BASE_DIR = rzkala-dashboard/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.core.mapper import load_and_map
from src.core.analyzer import run_all_analyses
from src.core.exporter import export_results
from src.components.kpi_cards import get_kpi_cards, print_kpi_cards
from src.components.funnel_chart import get_funnel_data, print_funnel


def resolve_path(user_input):
    """تبدیل ورودی کاربر به مسیر مطلق معتبر"""
    if not user_input:
        return None

    user_input = user_input.strip().strip('"').strip("'")

    # مسیر مطلق
    if os.path.isabs(user_input):
        if os.path.exists(user_input):
            return user_input
        else:
            print(f"\n❌ فایل یافت نشد: {user_input}")
            return None

    # مسیر نسبی از پوشه پروژه
    full_path = os.path.join(BASE_DIR, user_input)
    if os.path.exists(full_path):
        return full_path

    print(f"\n❌ فایل یافت نشد: {user_input}")
    print(f"   چک شد: {full_path}")
    return None


def run_pipeline(file_path=None):
    """اجرای کامل پایپلاین تحلیل"""

    print("=" * 60)
    print("🧠 RzKala — موتور تحلیل فروش")
    print("=" * 60)

    # ۱. بارگذاری داده
    data = load_and_map(file_path=file_path)
    orders = data['orders']
    traffic = data['traffic']
    ad_spend = data['ad_spend']

    if file_path and data['mapping_log'] != '📌 دیتای دمو — بدون مپینگ':
        print(f"\n📋 گزارش مپینگ:\n{data['mapping_log']}")
#new
    print(f"\n📋 ستون‌های شناسایی‌شده: {orders.columns.tolist()}")
    print(f"📋 ردیف‌ها: {len(orders)}")
    print(f"📋 نمونه:\n{orders.head(2).to_string()}")

    # ۲. KPI
    kpi = get_kpi_cards(orders)
    print_kpi_cards(kpi)

    # ۳. قیف فروش
    funnel = get_funnel_data(orders, traffic)
    print_funnel(funnel)

    # ۴. تحلیل کامل با DuckDB
    results = run_all_analyses(
        orders_df=orders,
        traffic_df=traffic,
        ad_spend_df=ad_spend
    )

    # ۵. خروجی
    output_path = export_results(results)

    print(f"\n✅ پایپلاین کامل شد!")
    print(f"📁 خروجی: {output_path}")

    return results


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("📂 RzKala — بارگذاری فایل فروش")
    print("=" * 60)
    print("مسیر فایل رو وارد کن (مطلق یا نسبی از پوشه پروژه)")
    print("Enter بزن → دیتای دمو (RzKala Sample)")
    print("-" * 60)

    user_input = input("📂 مسیر: ").strip()
    file_path = resolve_path(user_input)

    if file_path is None and user_input:
        retry = input("\n🔁 دوباره امتحان کنی؟ (y/n): ").strip().lower()
        if retry == 'y':
            user_input = input("📂 مسیر: ").strip()
            file_path = resolve_path(user_input)

    run_pipeline(file_path=file_path)