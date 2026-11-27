# -*- coding: utf-8 -*-
"""
DuckDB 只读查询示例（模拟大模型工具调用）。

用法（在项目根目录执行）：
  .venv\\Scripts\\python.exe server\\query_duckdb_demo.py
  .venv\\Scripts\\python.exe server\\query_duckdb_demo.py "SELECT split, count(*) n FROM llm_samples GROUP BY 1"
"""

from __future__ import annotations

import re
import sys

import duckdb

from config import duckdb_warehouse as cfg

FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|ATTACH|COPY|EXPORT|PRAGMA|CALL|CREATE|REPLACE|GRANT)\b",
    re.I,
)


def run_sql(sql: str) -> None:
    sql = sql.strip().rstrip(";")
    if FORBIDDEN.search(sql):
        raise SystemExit("仅允许只读 SELECT 查询")
    if not sql.lower().lstrip().startswith("select"):
        raise SystemExit("仅允许以 SELECT 开头的语句")
    con = duckdb.connect(str(cfg.DB_PATH), read_only=True)
    try:
        df = con.execute(sql).df()
        print(df.to_string(index=False))
        print(f"\n({len(df)} rows)")
    finally:
        con.close()


def main():
    if not cfg.DB_PATH.exists():
        raise SystemExit(f"缺少 {cfg.DB_PATH}，请先运行 server\\build_duckdb_warehouse.py")
    sql = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "SELECT table_name, count(*) AS n_cols FROM schema_catalog GROUP BY 1 ORDER BY 1"
    )
    print("SQL:", sql)
    run_sql(sql)


if __name__ == "__main__":
    main()
