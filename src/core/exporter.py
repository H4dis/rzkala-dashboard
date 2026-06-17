import pandas as pd
import os
import json
from datetime import datetime

# ============================================================
# EXPORTER — خروجی گرفتن از تحلیل‌ها
# نسخه ۲ — با نمودار Plotly در HTML
# ============================================================

try:
    import plotly.express as px
    import plotly.io as pio

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DIR = os.path.join(BASE_DIR, 'data', 'sample')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')


def export_results(results, output_dir=None):
    """ذخیره نتایج تحلیل‌ها"""

    if output_dir is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(OUTPUT_DIR, f'report_{timestamp}')

    os.makedirs(output_dir, exist_ok=True)
    files_created = []

    # CSV
    for name, df in results.items():
        if df is not None and len(df) > 0:
            csv_path = os.path.join(output_dir, f'{name}.csv')
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            files_created.append(csv_path)

    # Excel
    excel_path = os.path.join(output_dir, 'report.xlsx')
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        for name, df in results.items():
            if df is not None and len(df) > 0:
                df.to_excel(writer, sheet_name=name, index=False)
    files_created.append(excel_path)

    # JSON
    summary = {}
    for name, df in results.items():
        if df is not None and len(df) > 0:
            df_preview = df.head(5).copy()
            for col in df_preview.columns:
                if pd.api.types.is_datetime64_any_dtype(df_preview[col]):
                    df_preview[col] = df_preview[col].astype(str)
            summary[name] = {
                'shape': list(df.shape),
                'columns': df.columns.tolist(),
                'preview': df_preview.to_dict(orient='records')
            }
    json_path = os.path.join(output_dir, 'summary.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    files_created.append(json_path)

    # HTML
    html_path = os.path.join(output_dir, 'report.html')
    _build_html_report(results, html_path)
    files_created.append(html_path)

    print(f"\n✅ گزارش در {output_dir} ذخیره شد:")
    for f in files_created:
        size_kb = os.path.getsize(f) / 1024
        print(f"   📄 {os.path.basename(f)} ({size_kb:.1f} KB)")

    return output_dir


def _build_html_report(results, html_path):
    """ساخت گزارش HTML با نمودار"""
    html_parts = []

    # KPI
    if 'kpi' in results and len(results['kpi']) > 0:
        kpi = results['kpi'].iloc[0]
        html_parts.append(f"""
        <div style="display:flex;gap:20px;flex-wrap:wrap;">
            <div class="kpi-card" style="background:#e8f5e9;padding:16px;border-radius:12px;flex:1;">
                <h3>💰 فروش کل</h3>
                <p style="font-size:24px;">{kpi['total_revenue']:,.0f} ریال</p>
            </div>
            <div class="kpi-card" style="background:#e3f2fd;padding:16px;border-radius:12px;flex:1;">
                <h3>📈 سود</h3>
                <p style="font-size:24px;">{kpi['total_profit']:,.0f} ریال</p>
            </div>
            <div class="kpi-card" style="background:#fff3e0;padding:16px;border-radius:12px;flex:1;">
                <h3>📦 سفارشات</h3>
                <p style="font-size:24px;">{kpi['total_orders']:,.0f}</p>
            </div>
        </div>
        """)

    # Funnel chart
    if 'funnel' in results and HAS_PLOTLY:
        fig = px.funnel(results['funnel'], x='count', y='stage', title='قیف فروش')
        html_parts.append(pio.to_html(fig, full_html=False))

    # Trend chart
    if 'trend' in results and HAS_PLOTLY:
        fig = px.line(results['trend'], x='date', y='revenue', title='روند فروش روزانه')
        html_parts.append(pio.to_html(fig, full_html=False))

    # ROAS table
    if 'roas' in results:
        html_parts.append("<h2>📢 ROAS</h2>")
        html_parts.append(results['roas'].to_html(index=False))

    # RFM table
    if 'rfm' in results:
        html_parts.append("<h2>👥 بخش‌بندی مشتریان</h2>")
        html_parts.append(results['rfm'].to_html(index=False))

    # Profitability
    if 'profitability' in results:
        html_parts.append("<h2>🏆 سودآوری محصولات</h2>")
        html_parts.append(results['profitability'].head(10).to_html(index=False))

    # Discount Impact
    if 'discount_impact' in results:
        html_parts.append("<h2>🏷️ تأثیر تخفیف</h2>")
        html_parts.append(results['discount_impact'].to_html(index=False))

    # Repeat Rate
    if 'repeat_rate' in results:
        html_parts.append("<h2>🔄 نرخ بازگشت مشتری</h2>")
        html_parts.append(results['repeat_rate'].to_html(index=False))

    full_html = f"""
    <html dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>RzKala Report</title>
        <style>
            body {{ font-family: Tahoma; background: #f5f5f5; padding: 40px; }}
            .kpi-card h3 {{ margin: 0; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; background: white; border-radius: 8px; overflow: hidden; }}
            th {{ background: #6200ea; color: white; padding: 12px; text-align: right; }}
            td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <h1>🧠 RzKala — گزارش تحلیل فروش</h1>
        {''.join(html_parts)}
    </body>
    </html>
    """

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)


if __name__ == '__main__':
    import sys

    sys.path.insert(0, os.path.join(BASE_DIR, 'src'))
    from mapper import load_and_map
    from analyzer import run_all_analyses

    print("🧪 تست exporter.py (v2) ...\n")
    data = load_and_map()
    results = run_all_analyses(
        orders_df=data['orders'],
        traffic_df=data['traffic'],
        ad_spend_df=data['ad_spend']
    )
    export_results(results)