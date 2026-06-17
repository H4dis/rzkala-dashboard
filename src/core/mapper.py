import pandas as pd
import os
import re
from difflib import get_close_matches

# ============================================================
# MAPPER — تشخیص و استانداردسازی ستون‌های فایل ورودی
# نسخه ۵ — aliasهای کامل برای همه دیتاست‌های رایج
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DIR = os.path.join(BASE_DIR, 'data', 'sample')

COLUMN_ALIASES = {
    'order_date': [
        'order_date', 'date', 'orderdate', 'order_datetime', 'datetime',
        'تاریخ', 'تاریخ_سفارش', 'تاریخ سفارش', 'تاریخ_فاکتور', 'تاریخ فاکتور',
        'invoice_date', 'invoicedate', 'sale_date', 'transaction_date', 'dt',
        'date_sale', 'date_of_order', 'order_date_time', 'order_date',
        'Order_Date', 'Order Date', 'order date',
    ],
    'product_name': [
        'product_name', 'product', 'item', 'name', 'productname', 'item_name',
        'نام_محصول', 'نام محصول', 'کالا', 'نام کالا', 'نام_کالا', 'محصول',
        'description', 'item_description', 'product_desc', 'desc',
        'stockcode', 'stock_code', 'sku', 'کد_کالا',
        'Product', 'Product_Name', 'product title', 'product_title',
    ],
    'quantity': [
        'quantity', 'qty', 'count', 'number', 'تعداد', 'تعداد_کالا', 'تعداد کالا',
        'qty_sold', 'units', 'volume', 'amount',
        'Quantity', 'Qty', 'Order_Quantity', 'order_quantity',
    ],
    'unit_price': [
        'unit_price', 'price', 'unitprice', 'single_price', 'item_price',
        'قیمت', 'قیمت_واحد', 'قیمت واحد', 'فی', 'مبلغ_واحد', 'مبلغ واحد',
        'unitprice', 'price_per_unit', 'rate', 'unit_cost_price',
        'Unit_Price', 'UnitPrice', 'unit price', 'Price', 'price',
    ],
    'total_price': [
    'Total_Sales', 'total_sales', 'Sales', 'sales', ],
    'unit_cost': [
        'unit_cost', 'cost', 'cost_price', 'purchase_price',
        'قیمت_خرید', 'قیمت خرید', 'تمام‌شده', 'قیمت_تمام_شده', 'cost_price',
        'Cost_Price', 'cost price', 'purchase_cost', 'buying_price',
    ],
    'customer_phone': [
        'customer_phone', 'phone', 'mobile', 'customer', 'phone_number',
        'customer_id', 'customerid', 'client_id', 'user_id',
        'شماره', 'موبایل', 'تلفن', 'مشتری', 'شماره_مشتری', 'شماره مشتری',
        'Customer_ID', 'CustomerID', 'customer id', 'Customer', 'Customer_Name',
        'Customer_Segment', 'customer_segment',
    ],
    'order_id': [
        'order_id', 'order', 'id', 'transaction_id', 'invoice', 'invoice_id',
        'invoiceno', 'invoice_no', 'bill_id', 'receipt_id', 'order_number',
        'شماره_سفارش', 'شماره سفارش', 'کد_سفارش', 'شماره_فاکتور', 'شماره فاکتور',
        'Order_ID', 'OrderID', 'Order Id', 'Transaction_ID', 'transaction id',
    ],
    'campaign': [
        'campaign', 'utm_campaign', 'camp', 'utm',
        'کمپین', 'منبع', 'کانال', 'تبلیغ', 'کد_کمپین',
        'Campaign', 'Marketing_Campaign', 'utm_source', 'source',
    ],
    'order_status': [
        'order_status', 'status', 'state',
        'وضعیت', 'وضعیت_سفارش', 'وضعیت سفارش',
        'Order_Status', 'OrderStatus', 'order state', 'Status',
    ],
    'category': [
        'category', 'cat', 'group', 'product_category',
        'دسته', 'دسته‌بندی', 'گروه', 'دسته بندی', 'گروه_کالا',
        'Category', 'Product_Category', 'product category', 'Product_Category',
        'Market', 'market', 'Region', 'region', 'segment',
    ],
    'profit': [
        'profit', 'Profit', 'net_profit', 'net_income',
        'سود', 'سود_خالص', 'درآمد_خالص', 'سود ویژه',
        'Net_Profit', 'net profit', 'Profit_Amount', 'income',
    ],
    'discount_pct': [
        'discount_pct', 'discount', 'off', 'takhfif',
        'تخفیف', 'درصد_تخفیف', 'درصد تخفیف',
        'Discount', 'discount', 'Discount_Amount', 'discount percentage',
    ],
    'total_price': [
        'total_price', 'total', 'amount', 'totalprice', 'sum', 'revenue',
        'gross_amount', 'net_amount', 'final_amount', 'total_amount',
        'total_income', 'gross_revenue', 'total_revenue', 'order_total',
        'sale_amount', 'sales', 'sales_amount', 'total_sales',
        'transaction_amount', 'payment', 'total_payment',
        'مبلغ_کل', 'مبلغ کل', 'جمع', 'قیمت_کل', 'قیمت کل', 'مبلغ',
        'جمع_کل', 'جمع کل', 'مبلغ_نهایی', 'مبلغ نهایی', 'درآمد', 'درآمد_کل', 'فروش', 'مبلغ_فروش',
        'price', 'value', 'total_value', 'grand_total',
        'Sales', 'sales', 'Revenue', 'revenue', 'Total', 'total',
        'Sales_Amount', 'sales_amount',
    ],
}

CAMPAIGN_SOURCE_MAP = {
    'g_': 'google', 'ig_': 'instagram', 'email_': 'email', 'direct': 'direct',
}


def strip_column_names(df):
    df.columns = df.columns.str.strip()
    return df


def detect_persian_date(series):
    if len(series.dropna()) == 0:
        return pd.to_datetime(series, errors='coerce')
    sample = str(series.dropna().iloc[0])
    if re.search(r'1[34]\d{2}[/-]', sample):
        try:
            from persiantools.jdatetime import JalaliDate
            dates = []
            for val in series:
                if pd.isna(val):
                    dates.append(pd.NaT)
                else:
                    val_str = str(val).replace('/', '-').strip()
                    parts = re.split(r'[-/\s]', val_str)
                    if len(parts) >= 3 and len(parts[0]) == 4:
                        jd = JalaliDate(int(parts[0]), int(parts[1]), int(parts[2]))
                        dates.append(jd.to_gregorian())
                    else:
                        dates.append(pd.NaT)
            return pd.to_datetime(dates)
        except ImportError:
            pass
    return pd.to_datetime(series, errors='coerce')


def find_column_match(file_columns, target_aliases):
    file_columns_lower = [str(c).strip().lower() for c in file_columns]

    for alias in target_aliases:
        alias_lower = alias.lower()
        if alias_lower in file_columns_lower:
            return file_columns[file_columns_lower.index(alias_lower)]

    for alias in target_aliases:
        alias_lower = alias.lower()
        for fc in file_columns:
            if alias_lower in str(fc).strip().lower():
                return fc

    return None


def detect_columns(df):
    file_columns = df.columns.tolist()
    mapping = {}
    log = []

    for standard_name, aliases in COLUMN_ALIASES.items():
        match = find_column_match(file_columns, aliases)
        if match:
            mapping[standard_name] = match
            log.append(f"  ✅ {standard_name} ← '{match}'")
        else:
            log.append(f"  ⚠️ {standard_name} ← not found")

    return mapping, log


def normalize_dataframe(df, mapping):
    df_norm = df.copy()
    renames = {v: k for k, v in mapping.items() if v in df.columns}
    df_norm = df_norm.rename(columns=renames)
    found_cols = [c for c in mapping.keys() if c in df_norm.columns]
    df_norm = df_norm[found_cols]
    return df_norm


def ensure_total_price(df):
    """If total_price missing, create from unit_price * quantity, or Sales, or profit"""
    if 'total_price' not in df.columns:
        if 'unit_price' in df.columns and 'quantity' in df.columns:
            df['total_price'] = df['unit_price'] * df['quantity']
            print("built: total_price = unit_price * quantity")
        elif 'unit_price' in df.columns:
            df['total_price'] = df['unit_price']
            print("built: total_price = unit_price (quantity=1 assumed)")
        elif 'profit' in df.columns and 'unit_cost' in df.columns:
            df['total_price'] = df['profit'] + (df['unit_cost'] * df['quantity'] if 'quantity' in df.columns else df['unit_cost'])
            print("built: total_price = profit + cost")
        else:
            print("WARNING: total_price not found and cannot be built!")
    return df


def fill_missing_cost(df):
    if 'unit_cost' not in df.columns:
        if 'unit_price' in df.columns:
            print("unit_cost not found. Estimated as 60% of unit_price (40% margin).")
            df['unit_cost'] = df['unit_price'] * 0.60
        elif 'total_price' in df.columns and 'profit' in df.columns and 'quantity' in df.columns:
            df['unit_cost'] = (df['total_price'] - df['profit']) / df['quantity']
            print("built: unit_cost = (total_price - profit) / quantity")
    return df


def load_and_map(file_path=None):
    if file_path is None or not os.path.exists(str(file_path)):
        print("No file uploaded. Using demo data (RzKala Sample).")
        orders = pd.read_csv(os.path.join(SAMPLE_DIR, 'orders.csv'))
        traffic = pd.read_csv(os.path.join(SAMPLE_DIR, 'traffic.csv'))
        ad_spend = pd.read_csv(os.path.join(SAMPLE_DIR, 'ad_spend.csv'))
        return {
            'orders': orders,
            'traffic': traffic,
            'ad_spend': ad_spend,
            'mapping_log': 'Using demo data',
        }

    file_ext = str(file_path).split('.')[-1].lower()
    if file_ext == 'csv':
        df = pd.read_csv(file_path)
    elif file_ext in ['xlsx', 'xls']:
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path, sep=None, engine='python')

    df = strip_column_names(df)

    print(f"\nFile: {file_path}")
    print(f"   {df.shape[0]:,} rows | {df.shape[1]} columns")
    print(f"   Columns: {df.columns.tolist()}")

    print("\nAuto-detection:")
    mapping, log = detect_columns(df)
    for line in log:
        print(line)

    df_norm = normalize_dataframe(df, mapping)
    df_norm = ensure_total_price(df_norm)

    if 'order_date' in df_norm.columns:
        try:
            df_norm['order_date'] = detect_persian_date(df_norm['order_date'])
            df_norm['order_date'] = df_norm['order_date'].dt.strftime('%Y-%m-%d')
            print("Date column standardized.")
        except Exception as e:
            print(f"Date warning: {e}")

    df_norm = fill_missing_cost(df_norm)

    if 'quantity' not in df_norm.columns:
        df_norm['quantity'] = 1

    print(f"\nOutput: {df_norm.shape[0]} rows | {df_norm.shape[1]} columns")
    print(f"   Final columns: {df_norm.columns.tolist()}")

    return {
        'orders': df_norm,
        'traffic': None,
        'ad_spend': None,
        'mapping_log': '\n'.join(log),
    }