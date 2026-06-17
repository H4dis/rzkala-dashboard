rzkala-dashboard/
├── README.md
├── requirements.txt          # duckdb, pandas, plotly, streamlit/dash (آخر انتخاب)
├── data/
│   ├── sample/               # دیتای دمو (ساختگی)
│   │   ├── orders.csv
│   │   ├── traffic.csv
│   │   └── ad_spend.csv
│   └── user_uploads/         # فایل‌های مشتری
├── src/
│   ├── data_generator.py     # ژنراتور دیتای فیک رزکالا
│   ├── mapper.py             # تشخیص هوشمند ستون‌ها + Fuzzy Matching
│   ├── analyzer.py           # موتور SQL با DuckDB (قیف، ROAS، RFM)
│   └── exporter.py           # خروجی CSV، Excel
├── dashboard/                # ← این پوشه رو آخر انتخاب می‌کنیم
│   └── app.py
└── assets/
    └── style.css
1-demo done- itis 2024 sample of beautify stuff and result save into data sample.csv3of them 

v2
# ساختار فایل اصلی Streamlit (که ما ازش یاد می‌گیریم)
app.py
├── st.set_page_config()           # تنظیمات صفحه
├── st.file_uploader()             # آپلود فایل
├── load_data()                    # تابع بارگذاری (sample یا user)
├── st.date_input() × 2            # فیلتر تاریخ
├── st.sidebar.multiselect() × 3   # فیلتر آبشاری
├── filter_data()                  # تابع فیلتر (ما بهترش می‌کنیم)
├── نمودارها:
│   ├── px.bar (Category Sales)
│   ├── px.pie (Region)
│   ├── px.line (Time Series)
│   ├── px.treemap (Hierarchy)
│   ├── px.scatter (Correlation)
│   └── go.Figure (Pivot Table)
├── expander + download button
└── st.plotly_chart()








rzkala-dashboard/
│
├── README.md                      # توضیحات پروژه
├── requirements.txt               # پیش‌نیازها
├── .gitignore                     # فایل‌های ignored
│
├── data/
│   ├── sample/                    # دیتای دمو (ساختگی)
│   │   ├── orders.csv
│   │   ├── traffic.csv
│   │   └── ad_spend.csv
│   └── user_uploads/              # فایل‌های آپلودی مشتری (آینده)
│       └── .gitkeep
│
├── src/
│   ├── core/                      # 🧠 مغز پروژه (مستقل از نمایش)
│   │   ├── __init__.py
│   │   ├── mapper.py              # تشخیص و استانداردسازی ستون‌ها
│   │   ├── analyzer.py            # موتور SQL با DuckDB
│   │   └── exporter.py            # خروجی CSV, Excel, HTML, JSON
│   │
│   ├── components/                # 🧩 کامپوننت‌های تحلیلی
│   │   ├── __init__.py
│   │   ├── kpi_cards.py           # کارت‌های KPI
│   │   ├── funnel_chart.py        # قیف فروش
│   │   └── filters.py             # فیلترهای زنجیره‌ای
│   │
│   ├── data_generator.py          # 🎲 ژنراتور دیتای فیک
│   └── main.py                    # 🚀 نقطه ورود اصلی
│
├── dashboard/                     # 📊 لایه نمایش (آینده)
│   ├── __init__.py
│   └── app.py                     # Streamlit / Dash
│
├── output/                        # 📁 خروجی‌های تحلیل
│   └── .gitkeep
│
├── tests/                         # 🧪 تست‌ها (آینده)
│   └── .gitkeep
│
├── scripts/                       # 🔧 اسکریپت‌های کمکی
│   └── run_all.py                 # اجرای همه تحلیلها یکجا
│
└── venv/                          # محیط مجازی (gitignore شده)