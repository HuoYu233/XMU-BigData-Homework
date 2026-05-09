"""Prompt templates for the Data Agent pipeline"""

TABLE_SELECTION_PROMPT = """You are a data analyst working with a Brazilian e-commerce database.

The database contains the following tables:
{table_summaries}

Given the user's question, select which tables are needed to answer it.
Return ONLY a comma-separated list of table names, nothing else.
If the question is about orders, you usually also need related tables (customers, order_items, etc.).

User question: {question}

Tables needed:"""

SQL_GENERATION_PROMPT = """You are an expert SQL developer working with a MySQL database.

## Database Schema
{schemas}

## Sample Data (first 3 rows per table)
{samples}

## Instructions
Generate a MySQL SELECT query to answer the user's question.
- Use proper JOINs between tables
- Use GROUP BY and ORDER BY as needed
- ALIAS column names for readability
- Return ONLY the SQL query, no explanation
- Do NOT use INSERT, UPDATE, DELETE, DROP or any write operations
- If the question is vague, make reasonable assumptions

## User Question
{question}

## SQL Query:"""

RESULT_INTERPRETATION_PROMPT = """You are a data analyst explaining query results to a business user.

## User Question
{question}

## SQL Used
{sql}

## Query Results
{results}

## Instructions
Provide a concise, business-relevant interpretation of the results in Chinese.
- Summarize key findings in 2-4 sentences
- Highlight notable trends or outliers
- Suggest follow-up questions if relevant
- Do NOT repeat the raw data verbatim

## Analysis (in Chinese):"""

SQL_FIX_PROMPT = """You are a MySQL expert fixing a SQL error.

## Database Schema
{schemas}

## Original Question
{question}

## Erroneous SQL
{sql}

## Error Message
{error}

## Instructions
Fix the SQL query to resolve the error. Return ONLY the corrected SQL query, no explanation.

## Fixed SQL:"""
