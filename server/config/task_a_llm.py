# -*- coding: utf-8 -*-
"""Task A · LLM 死亡风险微调数据集配置。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIDECAR = ROOT / "output" / "text_fields_sidecar.csv"
DEDUP = ROOT / "output" / "dedup_raw.csv"
# 复用表格 Task A 的划分与标签，保证患者不泄漏到测试集
SPLIT_PARTS = {
    "train": ROOT / "dataset" / "task_a" / "features_train.csv",
    "val": ROOT / "dataset" / "task_a" / "features_val.csv",
    "test": ROOT / "dataset" / "task_a" / "features_test.csv",
}
PATIENTS = ROOT / "dataset" / "task_a" / "patients.csv"
OUT_DIR = ROOT / "dataset" / "task_a_llm"

SEED = 42
MIN_CHARS = 40
MAX_INPUT_CHARS = 6000

INSTRUCTION = (
    "根据以下肝癌相关患者的基线病历，判断死亡风险。"
    "只回答 0 或 1：0=低风险/随访未死亡，1=高风险/发生死亡。"
    "不要编造病历中未出现的检查，不要输出除 0/1 以外的文字。"
)

SYSTEM_PROMPT = (
    "你是肝癌临床风险助手。根据基线就诊/入院时可用的病历文本判断死亡风险，"
    "只输出 0 或 1。严禁使用结局后信息。"
)

# (段落标题, 字段列表) — 按优先级；同段多字段用；拼接
TEXT_SECTIONS = [
    ("主诉", ["chief_complain"]),
    (
        "现病史",
        [
            "last_visit_history_of_present_illness",
            "present_illness_history",
        ],
    ),
    (
        "诊断",
        [
            "last_diagnosis",
            "main_diagnosis",
            "disease_name",
            "out_diagnosis_name",
            "icd10_name",
            "icd10_name_2",
            "pre_operative_diagnosis",
            "post_operative_diagnosis",
        ],
    ),
    ("阳性症状", ["positive_symptom"]),
    ("既往史", ["past_history"]),
    ("个人史", ["personal_history"]),
    ("家族史", ["family_history"]),
    ("基础病", ["pre_disease_name", "infectious_disease_name"]),
    ("检查结论", ["exam_conclusion", "auxiliary_exam"]),
    ("手术操作", ["surgical_name", "description"]),
    ("查体", ["physical_exam", "specialist_exam"]),
    ("影像病理", ["imaging_conclusion", "immunohistochemistry_result"]),
]

# 截断时优先砍掉的段落（从先到后）
TRIM_ORDER = ["查体", "影像病理", "手术操作", "个人史", "家族史", "既往史", "检查结论", "现病史"]

# 禁止拼进 input 的列名（双重保险）
FORBIDDEN_COLS = {
    "death",
    "death_reason",
    "death_time",
    "death_or_last_visit_date",
    "follow_up_days",
    "label_death",
    "name",
    "patient_id",
    "inpatient_no_id",
    "基线_inpatient_no_id",
}

# 可选：把少量表型写成【基线摘要】
USE_BASELINE_SUMMARY = True
BASELINE_SUMMARY_COLS = [
    "gender",
    "age",
    "is_hepatitis",
    "is_smoking",
    "is_drinking",
    "is_hypertension",
    "is_diabetes",
]
