# -*- coding: utf-8 -*-
"""DuckDB 分析仓库路径与表约定（供 LLM Text2SQL 查询）。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "warehouse"
DB_PATH = OUT_DIR / "hcc_llm.duckdb"

# 源数据
TASK_A_DIR = ROOT / "dataset" / "task_a"
TASK_A_LLM_DIR = ROOT / "dataset" / "task_a_llm"
SIDECAR = ROOT / "output" / "text_fields_sidecar.csv"
DEDUP = ROOT / "output" / "dedup_raw.csv"

# 给大模型看的表说明（可导出为 schema 提示）
TABLE_DOCS = {
    "patients": "患者主表：一人一行。含 label_death、split、队列与表型字段。主键 patient_sn。",
    "llm_samples": "LLM 微调样本：一人一行。含 instruction/input/output、split、label_death、input_chars。",
    "clinical_text": "病历文本旁路：主诉、现病史、诊断、查体等原文列。不含 death_reason 等泄漏列。",
    "text_features": "规则抽取的临床开关特征（癌栓、腹水、TACE 等 0/1）。",
    "schema_catalog": "数据字典：表名、列名、说明，供大模型查库前阅读。",
}

# clinical_text 禁止导入的列
FORBIDDEN_TEXT_COLS = {
    "death",
    "death_reason",
    "death_time",
    "death_or_last_visit_date",
    "follow_up_days",
    "name",
    "patient_id",
    "inpatient_no_id",
    "基线_inpatient_no_id",
}
