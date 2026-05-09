"""MySQL database connection manager and schema reader"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseManager:
    def __init__(self):
        self.config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "olist"),
            "charset": "utf8mb4",
        }
        self.conn = None

    def connect(self):
        self.conn = pymysql.connect(**self.config)
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()

    def get_all_tables(self):
        """Return list of all table names in the database."""
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables

    def get_table_ddl(self, table_name):
        """Return CREATE TABLE DDL for a given table."""
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result[1]
        return None

    def get_sample_rows(self, table_name, n=3):
        """Return first n rows as a list of dicts."""
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {n}")
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return [dict(zip(cols, row)) for row in rows]

    def get_table_schema_string(self, table_name):
        """Return a concise schema description string from DDL."""
        ddl = self.get_table_ddl(table_name)
        if not ddl:
            return ""
        lines = []
        for line in ddl.split("\n"):
            line = line.strip()
            if line.startswith("`"):
                lines.append(line.rstrip(","))
        return f"Table: {table_name}\n" + "\n".join(lines)

    def execute_query(self, sql, params=None):
        """Execute a SELECT query and return (columns, rows)."""
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return cols, rows

    def get_all_table_summaries(self):
        """Return table name → Chinese description mapping for prompt context."""
        return {
            "customers": "客户信息：customer_id, customer_unique_id, 邮编, 城市, 州",
            "sellers": "卖家信息：seller_id, 邮编, 城市, 州",
            "products": "商品信息：product_id, 类目名称, 重量(g), 长宽高(cm), 照片数量",
            "category_translation": "类目名称翻译：葡萄牙语→英语",
            "orders": "订单主表：order_id, customer_id, 订单状态, 购买时间, 批准时间, 发货时间, 送达时间, 预计送达时间",
            "order_items": "订单明细：order_id, order_item_id, product_id, seller_id, 发货期限, 价格, 运费",
            "order_payments": "支付信息：order_id, 支付序号, 支付方式, 分期数, 支付金额",
            "order_reviews": "评价信息：review_id, order_id, 评分(1-5), 评论标题, 评论内容, 评论时间, 回复时间",
            "geolocation": "地理位置：邮编, 纬度, 经度, 城市, 州",
        }
