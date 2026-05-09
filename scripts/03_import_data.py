"""数据导入脚本：将cleaned CSV批量导入MySQL"""
import pandas as pd
import pymysql
import os
import numpy as np
import time
from dotenv import load_dotenv
from tqdm import tqdm

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "olist"),
    "charset": "utf8mb4",
}

DATA_DIR = os.path.join(PROJECT_ROOT, "data", "cleaned")

IMPORT_ORDER = [
    ("customers",        "customers.csv"),
    ("sellers",          "sellers.csv"),
    ("products",         "products.csv"),
    ("category_translation", "category_translation.csv"),
    ("orders",           "orders.csv"),
    ("order_items",      "order_items.csv"),
    ("order_payments",   "order_payments.csv"),
    ("order_reviews",    "order_reviews.csv"),
    ("geolocation",      "geolocation.csv"),
]

TABLE_NAMES_CN = {
    "customers":              "客户信息",
    "sellers":                "卖家信息",
    "products":               "商品信息",
    "category_translation":   "类目翻译",
    "orders":                 "订单主表",
    "order_items":            "订单明细",
    "order_payments":         "支付信息",
    "order_reviews":          "评价信息",
    "geolocation":            "地理位置",
}


def import_table(conn, table_name, filepath):
    df = pd.read_csv(filepath)

    # geolocation: dedup by composite key so INSERT IGNORE + unique index match
    if table_name == "geolocation":
        n_before = len(df)
        df = df.drop_duplicates(
            subset=["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng"]
        )
        if len(df) < n_before:
            print(f"  ℹ️  pandas去重: {n_before:,} → {len(df):,}")

    # Convert NaN and NaT to None for MySQL compatibility
    df = df.replace({np.nan: None, pd.NaT: None})
    df = df.where(pd.notna(df), None)

    if "Unnamed: 0" in df.columns:
        df.drop(columns=["Unnamed: 0"], inplace=True)

    cursor = conn.cursor()
    cols = ", ".join(f"`{c}`" for c in df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    insert_sql = f"INSERT IGNORE INTO {table_name} ({cols}) VALUES ({placeholders})"

    batch_size = 5000
    total = len(df)
    cn_name = TABLE_NAMES_CN.get(table_name, table_name)

    pbar = tqdm(
        total=total,
        desc=f"  {table_name:<22s} ({cn_name})",
        unit="row",
        unit_scale=True,
        bar_format="{desc}  {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
        ncols=100,
    )

    for i in range(0, total, batch_size):
        batch = df.iloc[i : i + batch_size]
        values = [tuple(row) for row in batch.values]
        cursor.executemany(insert_sql, values)
        conn.commit()
        pbar.update(len(batch))

    pbar.close()

    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    db_count = cursor.fetchone()[0]
    csv_count = len(df)
    cursor.close()

    status = "✅" if db_count == csv_count else "⚠️"
    print(f"  {status} {cn_name}: CSV={csv_count:,}  →  MySQL={db_count:,}")


def main():
    conn = pymysql.connect(**DB_CONFIG)

    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + "  Olist 数据导入 — CSV → MySQL 批量写入".center(54) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    start_time = time.time()
    results = []

    for table_name, filename in IMPORT_ORDER:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  ⚠️  跳过 {table_name}: 文件不存在")
            continue
        import_table(conn, table_name, filepath)
        print()

    elapsed = time.time() - start_time
    print("─" * 60)
    print(f"  🎉 全部导入完成!  耗时 {elapsed:.1f}s")
    print("─" * 60)
    print()

    # Summary table
    print(f"  {'表名':<24s} {'CSV行数':>10s}  {'MySQL行数':>10s}  {'状态':>6s}")
    print(f"  {'─' * 24} {'─' * 10}  {'─' * 10}  {'─' * 6}")
    cursor = conn.cursor()
    for table_name, filename in IMPORT_ORDER:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            continue
        df = pd.read_csv(filepath)
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        db_count = cursor.fetchone()[0]
        csv_count = len(df)
        s = "✅" if db_count == csv_count else "⚠️"
        print(f"  {TABLE_NAMES_CN.get(table_name, table_name):<24s} {csv_count:>10,}  {db_count:>10,}  {s:>6s}")
    cursor.close()
    print()


if __name__ == "__main__":
    main()
