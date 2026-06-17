"""
Dataset Merger - Smart merge multiple sales datasets into one.
Handles different column names, formats, and structures.
"""

import pandas as pd
import os
from difflib import get_close_matches

# Column standardization mapping
MERGE_COLUMN_ALIASES = {
    'order_date': [
        'order_date', 'date', 'orderdate', 'Order Date', 'Order_Date',
        'order_datetime', 'datetime', 'sale_date', 'transaction_date',
        'تاریخ', 'تاریخ_سفارش', 'تاریخ فاکتور', 'date_sale', 'dt',
        'invoice_date', 'InvoiceDate', 'order_date_time',
    ],
    'product_name': [
        'product_name', 'product', 'item', 'name', 'productname',
        'Product Name', 'Product_Name', 'product_title', 'description',
        'item_name', 'item_description', 'نام_محصول', 'نام محصول', 'کالا',
    ],
    'quantity': [
        'quantity', 'qty', 'count', 'Quantity', 'Qty', 'number',
        'units', 'تعداد', 'تعداد_کالا', 'qty_sold', 'volume',
    ],
    'total_price': [
        'total_price', 'total', 'amount', 'Sales', 'sales', 'revenue',
        'Revenue', 'sale_amount', 'total_sales', 'gross_amount',
        'مبلغ_کل', 'مبلغ کل', 'فروش', 'درآمد', 'price', 'total_amount',
    ],
    'unit_price': [
        'unit_price', 'price', 'unitprice', 'single_price', 'Unit_Price',
        'UnitPrice', 'item_price', 'rate', 'قیمت', 'قیمت_واحد', 'فی',
    ],
    'unit_cost': [
        'unit_cost', 'cost', 'cost_price', 'purchase_price',
        'cost_price', 'Cost_Price', 'قیمت_خرید', 'قیمت تمام‌شده',
    ],
    'customer_id': [
        'customer_id', 'customer', 'CustomerID', 'customer_phone',
        'phone', 'user_id', 'client_id', 'مشتری', 'شماره_مشتری',
        'customer_email', 'email',
    ],
    'category': [
        'category', 'cat', 'group', 'Category', 'Product_Category',
        'product_category', 'دسته', 'دسته‌بندی', 'گروه', 'گروه_کالا',
    ],
    'region': [
        'region', 'Region', 'state', 'State', 'city', 'City',
        'market', 'Market', 'country', 'Country',
        'منطقه', 'استان', 'شهر', 'کشور',
    ],
    'channel': [
        'channel', 'source', 'utm_source', 'campaign', 'platform',
        'sales_channel', 'کانال', 'منبع', 'بستر',
    ],
    'discount': [
        'discount', 'discount_pct', 'Discount', 'off', 'takhfif',
        'تخفیف', 'درصد_تخفیف',
    ],
    'order_status': [
        'order_status', 'status', 'state', 'is_returned',
        'وضعیت', 'وضعیت_سفارش', 'returned', 'cancelled',
    ],
    'profit': [
        'profit', 'Profit', 'net_profit', 'سود', 'سود_خالص',
        'profit_amount', 'net_income',
    ],
}

# Priority columns for merge identification
MERGE_KEY_COLUMNS = ['order_date', 'total_price', 'product_name', 'customer_id']


def detect_best_column(df, aliases):
    """Find the best matching column in dataframe for given aliases."""
    df_cols_lower = {col.strip().lower(): col for col in df.columns}

    for alias in aliases:
        alias_lower = alias.strip().lower()

        # Exact match
        if alias_lower in df_cols_lower:
            return df_cols_lower[alias_lower]

        # Contains match
        for col_lower, col_original in df_cols_lower.items():
            if alias_lower in col_lower or col_lower in alias_lower:
                return col_original

    return None


def standardize_dataframe(df, source_name="unknown"):
    """
    Standardize a single dataframe column names.
    Returns standardized df + mapping log.
    """
    mapping = {}
    log = []

    for standard_name, aliases in MERGE_COLUMN_ALIASES.items():
        match = detect_best_column(df, aliases)
        if match:
            mapping[match] = standard_name
            log.append(f"  [{source_name}] {standard_name} ← '{match}'")

    df_std = df.rename(columns=mapping)

    # Keep only standardized columns
    std_cols = [col for col in df_std.columns if col in MERGE_COLUMN_ALIASES.keys()]
    df_std = df_std[std_cols]

    return df_std, log


def find_common_columns(dfs_standardized):
    """Find columns that exist in ALL dataframes."""
    if not dfs_standardized:
        return []

    common = set(dfs_standardized[0].columns)
    for df in dfs_standardized[1:]:
        common = common.intersection(set(df.columns))

    return list(common)


def merge_datasets(file_paths, keep_all_columns=True):
    """
    Main merge function.

    Parameters:
        file_paths: list of file paths (CSV, Excel)
        keep_all_columns: if True, keep all unique columns. if False, only common columns.

    Returns:
        merged DataFrame, merge log
    """

    all_logs = []
    standardized_dfs = []

    # Step 1: Load and standardize each file
    for i, file_path in enumerate(file_paths):
        if not os.path.exists(file_path):
            all_logs.append(f"  WARNING: File not found - {file_path}")
            continue

        # Load file
        ext = file_path.split('.')[-1].lower()
        try:
            if ext == 'csv':
                df = pd.read_csv(file_path)
            elif ext in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            elif ext == 'txt':
                df = pd.read_csv(file_path, sep=None, engine='python')
            else:
                all_logs.append(f"  WARNING: Unsupported format - {file_path}")
                continue
        except Exception as e:
            all_logs.append(f"  ERROR loading {file_path}: {str(e)}")
            continue

        # Standardize
        source_name = os.path.basename(file_path)
        df_std, log = standardize_dataframe(df, source_name)

        if len(df_std.columns) == 0:
            all_logs.append(f"  WARNING: No matching columns in {source_name}")
            continue

        # Add source file info
        df_std['source_file'] = source_name

        standardized_dfs.append(df_std)
        all_logs.extend(log)
        all_logs.append(f"  [{source_name}] {len(df_std)} rows, {len(df_std.columns)} columns standardized")

    if len(standardized_dfs) == 0:
        return pd.DataFrame(), all_logs

    if len(standardized_dfs) == 1:
        return standardized_dfs[0], all_logs

    # Step 2: Find common columns
    common_cols = find_common_columns(standardized_dfs)
    all_logs.append(f"\n  Common columns across all files: {common_cols}")

    # Step 3: Determine merge columns
    if keep_all_columns:
        # Get all unique columns across all dataframes
        all_columns = []
        for df in standardized_dfs:
            all_columns.extend(df.columns.tolist())
        merge_cols = list(set(all_columns))
    else:
        merge_cols = common_cols + ['source_file']

    # Step 4: Align all dataframes to same columns before concat
    aligned_dfs = []
    for df in standardized_dfs:
        # Add missing columns with NaN
        for col in merge_cols:
            if col not in df.columns:
                df[col] = pd.NA
        aligned_dfs.append(df[merge_cols])

    # Step 5: Concat
    merged = pd.concat(aligned_dfs, ignore_index=True)

    # Step 6: Remove exact duplicates
    before_dedup = len(merged)
    merged = merged.drop_duplicates()
    after_dedup = len(merged)

    if before_dedup > after_dedup:
        all_logs.append(f"\n  Removed {before_dedup - after_dedup} duplicate rows")

    # Step 7: Sort by date if available
    if 'order_date' in merged.columns:
        try:
            merged['order_date'] = pd.to_datetime(merged['order_date'], errors='coerce')
            merged = merged.sort_values('order_date').reset_index(drop=True)
        except:
            pass

    all_logs.append(f"\n  MERGE COMPLETE: {len(merged)} total rows, {len(merged.columns)} columns")
    all_logs.append(f"  Source files: {[os.path.basename(f) for f in file_paths]}")

    return merged, all_logs


def merge_from_dataframes(dfs_dict, keep_all_columns=True):
    """
    Merge already-loaded dataframes.
    Returns: merged DataFrame, merge log, missing columns report
    """
    standardized_dfs = []
    all_logs = []
    missing_report = {}

    # Step 1: Standardize each dataframe
    for name, df in dfs_dict.items():
        df_std, log = standardize_dataframe(df, name)
        if len(df_std.columns) > 0:
            df_std['source_file'] = name
            standardized_dfs.append(df_std)
            all_logs.extend(log)
        else:
            all_logs.append(f"  WARNING: No matching columns in {name}")

    if len(standardized_dfs) == 0:
        all_logs.append("ERROR: No valid dataframes to merge.")
        return pd.DataFrame(), all_logs, {}

    if len(standardized_dfs) == 1:
        df = standardized_dfs[0]
        # Report available columns
        available = df.columns.tolist()
        for std_col in MERGE_COLUMN_ALIASES.keys():
            if std_col not in available:
                missing_report[std_col] = "not found in any file"
        return df, all_logs, missing_report

    # Step 2: Find common and all columns
    all_columns_set = set()
    for df in standardized_dfs:
        all_columns_set.update(df.columns.tolist())

    common_cols = list(set.intersection(*[set(df.columns) for df in standardized_dfs]))
    all_columns = sorted(list(all_columns_set))

    # Step 3: Report missing columns
    for std_col in MERGE_COLUMN_ALIASES.keys():
        files_with_col = []
        files_without = []
        for df in standardized_dfs:
            src = df['source_file'].iloc[0] if 'source_file' in df.columns else 'unknown'
            if std_col in df.columns:
                files_with_col.append(src)
            else:
                files_without.append(src)

        if len(files_with_col) == 0:
            missing_report[std_col] = f"not found in any file"
        elif len(files_without) > 0:
            missing_report[std_col] = f"found in {files_with_col}, missing in {files_without}"

    all_logs.append(f"\n  Common columns: {common_cols}")
    all_logs.append(f"  All unique columns: {all_columns}")
    all_logs.append(f"  Missing columns: {list(missing_report.keys())}")

    # Step 4: Keep columns
    if keep_all_columns:
        merge_cols = all_columns
    else:
        merge_cols = common_cols + ['source_file']

    # Step 5: Align and concat
    aligned_dfs = []
    for df in standardized_dfs:
        for col in merge_cols:
            if col not in df.columns:
                df[col] = pd.NA
        aligned_dfs.append(df[merge_cols])

    merged = pd.concat(aligned_dfs, ignore_index=True)
    merged = merged.drop_duplicates()

    # Step 6: Sort by date if available
    if 'order_date' in merged.columns:
        try:
            merged['order_date'] = pd.to_datetime(merged['order_date'], errors='coerce')
            merged = merged.sort_values('order_date').reset_index(drop=True)
        except:
            pass

    all_logs.append(f"\n  MERGE COMPLETE: {len(merged)} rows, {len(merged.columns)} columns")
    all_logs.append(f"  Source files: {list(dfs_dict.keys())}")

    return merged, all_logs, missing_report
# ============================================================
# Quick test
# ============================================================
if __name__ == '__main__':
    import os

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    SAMPLE_DIR = os.path.join(BASE_DIR, 'data', 'sample')

    # Test with sample files
    test_files = [
        os.path.join(SAMPLE_DIR, 'orders.csv'),
    ]

    print("=" * 60)
    print("MERGER TEST")
    print("=" * 60)

    merged, logs = merge_datasets(test_files)

    for log in logs:
        print(log)

    if len(merged) > 0:
        print(f"\nMerged DataFrame:")
        print(f"  Shape: {merged.shape}")
        print(f"  Columns: {merged.columns.tolist()}")
        print(f"\nFirst 3 rows:")
        print(merged.head(3).to_string())