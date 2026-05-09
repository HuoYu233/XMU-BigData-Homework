"""Data Agent Pipeline: orchestrates the 5-step query flow"""
import re
from .db import DatabaseManager
from .llm import DeepSeekLLM
from .prompts import (
    TABLE_SELECTION_PROMPT,
    SQL_GENERATION_PROMPT,
    RESULT_INTERPRETATION_PROMPT,
    SQL_FIX_PROMPT,
)

FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|GRANT|REVOKE|LOAD|RENAME|CALL|EXECUTE|EXEC)\b",
    re.IGNORECASE,
)


class AgentPipeline:
    def __init__(self):
        self.db = DatabaseManager()
        self.llm = DeepSeekLLM(temperature=0.1)

    def connect(self):
        self.db.connect()

    def close(self):
        self.db.close()

    def run(self, question: str):
        """Execute the full pipeline. Returns a dict with all step results."""
        result = {
            "question": question,
            "selected_tables": [],
            "sql": "",
            "security_check": "",
            "columns": [],
            "rows": [],
            "interpretation": "",
            "retry_count": 0,
            "error": None,
        }

        # Step 1: Table selection
        result["selected_tables"] = self._select_tables(question)

        # Step 2: SQL generation
        sql = self._generate_sql(question, result["selected_tables"])
        result["sql"] = sql

        # Step 3: Security check
        result["security_check"] = self._check_sql(sql)

        # Step 4: Execute with retry
        columns, rows, retries, error = self._execute_with_retry(
            question, sql, result["selected_tables"]
        )
        result["columns"] = columns
        result["rows"] = rows
        result["retry_count"] = retries
        if error:
            result["error"] = error
            return result

        # Step 5: Interpret results
        result["interpretation"] = self._interpret_results(
            question, sql, columns, rows
        )

        return result

    def _select_tables(self, question):
        all_tables = self.db.get_all_tables()
        summaries = self.db.get_all_table_summaries()
        summary_text = "\n".join(
            f"- {t}: {summaries.get(t, '')}" for t in all_tables
        )

        response = self.llm.invoke(
            TABLE_SELECTION_PROMPT.format(
                table_summaries=summary_text,
                question=question,
            ),
            "",
        )

        tables = [t.strip() for t in response.strip().split(",")]
        valid_tables = [t for t in tables if t in all_tables]
        return valid_tables if valid_tables else all_tables[:6]

    def _generate_sql(self, question, tables):
        schemas = "\n\n".join(
            self.db.get_table_schema_string(t) for t in tables
        )
        samples = "\n\n".join(
            f"--- {t} ---\n{self.db.get_sample_rows(t)}"
            for t in tables
        )

        response = self.llm.invoke(
            SQL_GENERATION_PROMPT.format(
                schemas=schemas,
                samples=samples,
                question=question,
            ),
            "",
        )

        sql = response.strip()
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0].strip()
        return sql

    def _check_sql(self, sql):
        if FORBIDDEN_SQL.search(sql):
            match = FORBIDDEN_SQL.search(sql)
            return f"❌ 安全拦截: 检测到危险操作 '{match.group(1)}'"
        if not sql.strip().upper().startswith(("SELECT", "WITH")):
            return f"❌ 安全拦截: 只允许 SELECT 或 WITH(CTE) 查询"
        return "✅ 安全检查通过"

    def _execute_with_retry(self, question, sql, tables, max_retries=3):
        retries = 0
        current_sql = sql

        while retries <= max_retries:
            try:
                cols, rows = self.db.execute_query(current_sql)
                return cols, rows, retries, None
            except Exception as e:
                retries += 1
                if retries > max_retries:
                    return [], [], retries, str(e)

                schemas = "\n\n".join(
                    self.db.get_table_schema_string(t) for t in tables
                )
                fix_response = self.llm.invoke(
                    SQL_FIX_PROMPT.format(
                        schemas=schemas,
                        question=question,
                        sql=current_sql,
                        error=str(e),
                    ),
                    "",
                )

                current_sql = fix_response.strip()
                if "```sql" in current_sql:
                    current_sql = current_sql.split("```sql")[1].split("```")[0].strip()
                elif "```" in current_sql:
                    current_sql = current_sql.split("```")[1].split("```")[0].strip()

                if FORBIDDEN_SQL.search(current_sql):
                    return [], [], retries, "修复后的 SQL 包含危险操作"

        return [], [], retries, "超过最大重试次数"

    def _interpret_results(self, question, sql, columns, rows):
        if not rows:
            return "查询未返回任何结果，请检查问题条件是否合理。"

        max_rows = 50
        display_rows = rows[:max_rows]
        results_text = "; ".join(str(list(row)) for row in display_rows)
        if len(rows) > max_rows:
            results_text += f"\n... (共 {len(rows)} 行，仅展示前 {max_rows} 行)"

        cols_text = ", ".join(columns)
        full_results = f"Columns: {cols_text}\nRows: {results_text}"

        return self.llm.invoke(
            RESULT_INTERPRETATION_PROMPT.format(
                question=question,
                sql=sql,
                results=full_results,
            ),
            "",
        )
