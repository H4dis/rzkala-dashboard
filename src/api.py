"""
RzKala API — FastAPI
Endpoints برای تحلیل فروش
"""

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
import pandas as pd
import os
import sys
import io
from datetime import datetime

# تنظیم مسیر
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.core.mapper import load_and_map
from src.core.analyzer import run_all_analyses

app = FastAPI(
    title="RzKala Analytics API",
    description="موتور تحلیل فروش — آپلود فایل، دریافت KPI، قیف فروش، ROAS، RFM و...",
    version="1.0.0",
)

# ============================================================
# Global state — نتایج آخرین تحلیل
# ============================================================
current_results = {}
current_data = {}


# ============================================================
# POST — آپلود فایل
# ============================================================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """آپلود فایل CSV یا Excel فروش"""
    global current_results, current_data

    # خواندن فایل
    content = await file.read()
    file_ext = file.filename.split('.')[-1].lower()

    if file_ext == 'csv':
        df = pd.read_csv(io.BytesIO(content))
    elif file_ext in ['xlsx', 'xls']:
        df = pd.read_excel(io.BytesIO(content))
    else:
        return JSONResponse({"error": "فقط CSV و Excel پشتیبانی می‌شود."}, status_code=400)

    # ذخیره موقت
    temp_path = os.path.join(BASE_DIR, 'data', 'user_uploads', file.filename)
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    with open(temp_path, 'wb') as f:
        f.write(content)

    # بارگذاری با mapper
    data = load_and_map(file_path=temp_path)
    current_data = data

    # اجرای تحلیل
    results = run_all_analyses(
        orders_df=data['orders'],
        traffic_df=data['traffic'],
        ad_spend_df=data['ad_spend']
    )
    current_results = results

    # خلاصه
    kpi = results.get('kpi', pd.DataFrame())
    summary = {
        "filename": file.filename,
        "rows": len(data['orders']),
        "columns": data['orders'].columns.tolist(),
        "mapping_log": data['mapping_log'],
    }
    if len(kpi) > 0:
        summary["kpi"] = kpi.iloc[0].to_dict()

    return {"status": "ok", "summary": summary}


# ============================================================
# POST — آپلود چند فایل (orders + traffic + ad_spend)
# ============================================================
@app.post("/upload/multi")
async def upload_multi(
        orders: UploadFile = File(None),
        traffic: UploadFile = File(None),
        ad_spend: UploadFile = File(None),
):
    """آپلود همزمان فایل فروش، ترافیک و هزینه تبلیغات"""
    global current_results, current_data

    data = {'orders': None, 'traffic': None, 'ad_spend': None}

    if orders:
        content = await orders.read()
        temp_path = os.path.join(BASE_DIR, 'data', 'user_uploads', orders.filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, 'wb') as f:
            f.write(content)
        data = load_and_map(file_path=temp_path)
    else:
        data = load_and_map()

    if traffic:
        content = await traffic.read()
        traffic_df = pd.read_csv(io.BytesIO(content))
        data['traffic'] = traffic_df

    if ad_spend:
        content = await ad_spend.read()
        ad_spend_df = pd.read_csv(io.BytesIO(content))
        data['ad_spend'] = ad_spend_df

    current_data = data
    results = run_all_analyses(
        orders_df=data['orders'],
        traffic_df=data['traffic'],
        ad_spend_df=data['ad_spend']
    )
    current_results = results

    return {"status": "ok", "analyses_available": list(results.keys())}


# ============================================================
# GET — KPI
# ============================================================
@app.get("/api/kpi")
def get_kpi():
    if 'kpi' not in current_results:
        return {"error": "ابتدا فایل آپلود کنید: POST /upload"}
    kpi = current_results['kpi']
    return kpi.iloc[0].to_dict() if len(kpi) > 0 else {}


# ============================================================
# GET — Time Series روزانه
# ============================================================
@app.get("/api/trend")
def get_trend():
    if 'trend' not in current_results:
        return {"error": "ابتدا فایل آپلود کنید"}
    return current_results['trend'].to_dict(orient='records')


# ============================================================
# GET — Time Series هفتگی
# ============================================================
@app.get("/api/trend/weekly")
def get_trend_weekly():
    if 'trend_weekly' not in current_results:
        return {"error": "ابتدا فایل آپلود کنید"}
    return current_results['trend_weekly'].to_dict(orient='records')


# ============================================================
# GET — قیف فروش
# ============================================================
@app.get("/api/funnel")
def get_funnel():
    if 'funnel' not in current_results:
        return {"error": "داده ترافیک موجود نیست. فایل traffic.csv را آپلود کنید."}
    return current_results['funnel'].to_dict(orient='records')


# ============================================================
# GET — ROAS
# ============================================================
@app.get("/api/roas")
def get_roas():
    if 'roas' not in current_results:
        return {"error": "داده تبلیغات و ترافیک موجود نیست."}
    return current_results['roas'].to_dict(orient='records')


# ============================================================
# GET — RFM
# ============================================================
@app.get("/api/rfm")
def get_rfm():
    if 'rfm' not in current_results:
        return {"error": "داده مشتری (customer_phone) موجود نیست."}
    return current_results['rfm'].to_dict(orient='records')


# ============================================================
# GET — سودآوری (Pareto)
# ============================================================
@app.get("/api/profitability")
def get_profitability(limit: int = Query(20, description="تعداد محصولات برتر")):
    if 'profitability' not in current_results:
        return {"error": "ابتدا فایل آپلود کنید"}
    return current_results['profitability'].head(limit).to_dict(orient='records')


# ============================================================
# GET — TreeMap
# ============================================================
@app.get("/api/treemap")
def get_treemap(limit: int = Query(50, description="تعداد آیتم")):
    if 'treemap_data' not in current_results:
        return {"error": "ابتدا فایل آپلود کنید"}
    return current_results['treemap_data'].head(limit).to_dict(orient='records')


# ============================================================
# GET — Scatter
# ============================================================
@app.get("/api/scatter")
def get_scatter(limit: int = Query(100, description="تعداد آیتم")):
    if 'scatter_data' not in current_results:
        return {"error": "ابتدا فایل آپلود کنید"}
    return current_results['scatter_data'].head(limit).to_dict(orient='records')


# ============================================================
# GET — Repeat Rate
# ============================================================
@app.get("/api/repeat_rate")
def get_repeat_rate():
    if 'repeat_rate' not in current_results:
        return {"error": "داده مشتری موجود نیست."}
    return current_results['repeat_rate'].to_dict(orient='records')


# ============================================================
# GET — دانلود Excel
# ============================================================
@app.get("/api/export/excel")
def export_excel():
    if not current_results:
        return {"error": "ابتدا فایل آپلود کنید"}

    from src.core.exporter import export_results
    output_path = export_results(current_results)
    excel_path = os.path.join(output_path, 'report.xlsx')

    return FileResponse(
        excel_path,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename='rzkala_report.xlsx'
    )


# ============================================================
# GET — دانلود CSV یک تحلیل خاص
# ============================================================
@app.get("/api/export/csv/{name}")
def export_csv(name: str):
    if name not in current_results:
        return {"error": f"'{name}' موجود نیست.可用: {list(current_results.keys())}"}

    df = current_results[name]
    csv_content = df.to_csv(index=False, encoding='utf-8-sig')

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type='text/csv',
        headers={"Content-Disposition": f"attachment; filename={name}.csv"}
    )


# ============================================================
# Health check
# ============================================================
@app.get("/")
def root():
    return {
        "app": "RzKala Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
        "available_analyses": list(current_results.keys()),
        "data_source": current_data.get('mapping_log', 'No data loaded') if current_data else "No data loaded"
    }


# ============================================================
# Run
# ============================================================
if __name__ == '__main__':
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)