"""数据预处理脚本：读取原始CSV → 清洗 → 输出cleaned CSV"""
import pandas as pd
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "cleaned")

os.makedirs(OUTPUT_DIR, exist_ok=True)

FILES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

DATE_COLS = {
    "orders": [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
    "order_items": ["shipping_limit_date"],
}

print("=" * 60)
print("OLIST 数据预处理开始")
print("=" * 60)

for name, filename in FILES.items():
    filepath = os.path.join(DATASET_DIR, filename)
    print(f"\n--- 处理: {filename} ---")

    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df.columns = [col.strip().strip('"') for col in df.columns]
    before = len(df)

    pk_map = {
        "customers": "customer_id",
        "geolocation": ["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng"],
        "order_items": ["order_id", "order_item_id"],
        "order_payments": ["order_id", "payment_sequential"],
        "order_reviews": "review_id",
        "orders": "order_id",
        "products": "product_id",
        "sellers": "seller_id",
        "category_translation": "product_category_name",
    }
    pk = pk_map.get(name)
    if pk:
        if isinstance(pk, list):
            dupe_mask = df.duplicated(subset=pk)
        else:
            dupe_mask = df.duplicated(subset=[pk])
        dupes = dupe_mask.sum()
        if dupes > 0:
            print(f"  发现 {dupes} 条重复记录，已删除")
            df = df[~dupe_mask]

    nulls = df.isnull().sum()
    null_cols = nulls[nulls > 0]
    if len(null_cols):
        for col, cnt in null_cols.items():
            pct = cnt / len(df) * 100
            print(f"  缺失值 [{col}]: {cnt} ({pct:.1f}%)")
    else:
        print(f"  缺失值: 无")

    for col in DATE_COLS.get(name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    out_path = os.path.join(OUTPUT_DIR, f"{name}.csv")
    df.to_csv(out_path, index=False)
    after = len(df)
    print(f"  行数: {before} → {after} (去重后), 列数: {len(df.columns)}")
    print(f"  保存至: {out_path}")

print("\n" + "=" * 60)
print("预处理完成！清洗后数据保存在 data/cleaned/")
print("=" * 60)
