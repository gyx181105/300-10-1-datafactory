# -*- coding: utf-8 -*-
"""
Task A · 构建大语言模型微调数据集（病历原文 → 死亡风险 0/1）

依赖：
  - output/text_fields_sidecar.csv
  - dataset/task_a/features_{train,val,test}.csv（划分与标签；若无则先跑 build_task_a.py）

输出：dataset/task_a_llm/*.jsonl

用法（在项目根目录执行）：
  set PYTHONNOUSERSITE=1
  python server\\build_llm_dataset_a.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config import task_a_llm as cfg

EMPTY = {"", "nan", "none", "null", "na", "n/a", "-", "—", "无", "未见", "不详", "未知"}


def _clean(v: Any) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    s = str(v).strip()
    if s.lower() in EMPTY or s in EMPTY:
        return ""
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _dedupe_join(parts: list[str], sep: str = "；") -> str:
    seen = set()
    out = []
    for p in parts:
        p = _clean(p)
        if not p or p in seen:
            continue
        seen.add(p)
        out.append(p)
    return sep.join(out)


def load_splits() -> pd.DataFrame:
    want = {
        "patient_sn",
        "label_death",
        "split",
        "cohort_hcc_strong",
        "label_uncertain",
        "gender",
        "age",
        "is_hepatitis",
        "is_smoking",
        "is_drinking",
        "is_hypertension",
        "is_diabetes",
    }
    frames = []
    for split, path in cfg.SPLIT_PARTS.items():
        if not path.exists():
            raise SystemExit(
                f"缺少 {path}。请先运行：python server\\build_task_a.py（仅用于划分/标签）"
            )
        header = list(pd.read_csv(path, nrows=0).columns)
        use = [c for c in header if c in want]
        df = pd.read_csv(path, dtype=str, usecols=use)
        if "split" not in df.columns:
            df["split"] = split
        frames.append(df)
    all_df = pd.concat(frames, ignore_index=True)
    all_df["patient_sn"] = all_df["patient_sn"].astype(str)
    all_df["label_death"] = pd.to_numeric(all_df["label_death"], errors="coerce")
    all_df = all_df[all_df["label_death"].isin([0, 1])].copy()
    all_df["label_death"] = all_df["label_death"].astype(int)
    all_df = all_df.drop_duplicates("patient_sn", keep="first")
    print(f"划分加载: {len(all_df)} 人", all_df["split"].value_counts().to_dict())
    return all_df


def load_text() -> pd.DataFrame:
    if not cfg.SIDECAR.exists():
        raise SystemExit(f"缺少 {cfg.SIDECAR}，请先运行 server\\build_training_dataset.py")
    print("读取", cfg.SIDECAR)
    df = pd.read_csv(cfg.SIDECAR, dtype=str, low_memory=False)
    df["patient_sn"] = df["patient_sn"].astype(str)
    # 去掉禁止列
    drop = [c for c in df.columns if c in cfg.FORBIDDEN_COLS]
    if drop:
        df = df.drop(columns=drop, errors="ignore")
    df = df.drop_duplicates("patient_sn", keep="first")
    print(f"  文本旁路 rows={len(df)}")
    return df


def baseline_summary(row: pd.Series) -> str:
    if not cfg.USE_BASELINE_SUMMARY:
        return ""
    bits = []
    g = _clean(row.get("gender"))
    if g in {"1", "1.0"}:
        bits.append("性别：男")
    elif g in {"0", "0.0"}:
        bits.append("性别：女")
    age = _clean(row.get("age"))
    if age:
        try:
            bits.append(f"年龄：{int(float(age))}岁")
        except ValueError:
            bits.append(f"年龄：{age}")
    flag_map = {
        "is_hepatitis": "肝炎",
        "is_smoking": "吸烟",
        "is_drinking": "饮酒",
        "is_hypertension": "高血压",
        "is_diabetes": "糖尿病",
    }
    for col, name in flag_map.items():
        v = _clean(row.get(col))
        if v in {"1", "1.0"}:
            bits.append(f"{name}：是")
        elif v in {"0", "0.0"}:
            bits.append(f"{name}：否")
    return "，".join(bits)


def build_sections(text_row: pd.Series) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    for title, cols in cfg.TEXT_SECTIONS:
        vals = [_clean(text_row.get(c, "")) for c in cols if c not in cfg.FORBIDDEN_COLS]
        body = _dedupe_join([v for v in vals if v])
        if body:
            sections.append((title, body))
    return sections


def render_input(summary: str, sections: list[tuple[str, str]], max_chars: int) -> str:
    parts = []
    if summary:
        parts.append(f"【基线摘要】{summary}")
    for title, body in sections:
        parts.append(f"【{title}】{body}")
    text = "\n".join(parts)

    if len(text) <= max_chars:
        return text

    # 按 TRIM_ORDER 逐步截断段落
    sec_map = {t: b for t, b in sections}
    order = [t for t, _ in sections]
    for trim_title in cfg.TRIM_ORDER:
        if trim_title not in sec_map:
            continue
        # 先删整段
        sec_map.pop(trim_title, None)
        order = [t for t in order if t in sec_map]
        rebuilt = []
        if summary:
            rebuilt.append(f"【基线摘要】{summary}")
        for t in order:
            rebuilt.append(f"【{t}】{sec_map[t]}")
        text = "\n".join(rebuilt)
        if len(text) <= max_chars:
            return text

    # 仍超长：硬截断尾部
    return text[: max_chars - 1] + "…"


def make_records(meta: pd.DataFrame, text: pd.DataFrame) -> list[dict[str, Any]]:
    merged = meta.merge(text, on="patient_sn", how="left", suffixes=("", "_txt"))
    records = []
    skipped_short = 0
    for _, row in merged.iterrows():
        sections = build_sections(row)
        summary = baseline_summary(row)
        content = render_input(summary, sections, cfg.MAX_INPUT_CHARS)
        if len(content.replace(" ", "").replace("\n", "")) < cfg.MIN_CHARS:
            skipped_short += 1
            continue
        label = int(row["label_death"])
        out_str = str(label)
        rec = {
            "patient_sn": row["patient_sn"],
            "split": row["split"],
            "label_death": label,
            "instruction": cfg.INSTRUCTION,
            "input": content,
            "output": out_str,
            "messages": [
                {"role": "system", "content": cfg.SYSTEM_PROMPT},
                {"role": "user", "content": content},
                {"role": "assistant", "content": out_str},
            ],
            "meta": {
                "input_chars": len(content),
                "n_sections": len(sections),
                "cohort_hcc_strong": row.get("cohort_hcc_strong"),
                "label_uncertain": row.get("label_uncertain"),
            },
        }
        records.append(rec)
    print(f"可用样本 {len(records)}；因文本过短跳过 {skipped_short}")
    return records


def write_jsonl(path: Path, rows: list[dict], mode: str) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            if mode == "alpaca":
                obj = {
                    "patient_sn": r["patient_sn"],
                    "split": r["split"],
                    "label_death": r["label_death"],
                    "instruction": r["instruction"],
                    "input": r["input"],
                    "output": r["output"],
                }
            else:
                obj = {
                    "patient_sn": r["patient_sn"],
                    "split": r["split"],
                    "label_death": r["label_death"],
                    "messages": r["messages"],
                }
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def audit_leakage(records: list[dict]) -> dict:
    """抽查 input 是否含明显泄漏词。"""
    # 结局泄漏（排除「家族史…死因不详」这类合法表述）
    bad_pat = re.compile(
        r"死亡原因|death_reason|随访天数|(?<!父)(?<!母)(?<!父母)(?<!哥哥)(?<!弟弟)(?<!姐姐)(?<!妹妹)患者死亡|(?<!父)(?<!母)已死亡"
    )
    hits = []
    for r in records:
        if bad_pat.search(r["input"]):
            hits.append(r["patient_sn"])
            if len(hits) >= 20:
                break
    return {
        "leakage_keyword_hits_sample": hits,
        "n_flagged_sample": len(hits),
        "note": "家族史中的「死因不详」不算泄漏",
    }


def main():
    meta = load_splits()
    text = load_text()
    records = make_records(meta, text)
    if not records:
        raise SystemExit("无可用 LLM 样本")

    cfg.OUT_DIR.mkdir(parents=True, exist_ok=True)
    by_split: dict[str, list] = {"train": [], "val": [], "test": []}
    for r in records:
        by_split.setdefault(r["split"], []).append(r)

    for split, rows in by_split.items():
        write_jsonl(cfg.OUT_DIR / f"{split}.alpaca.jsonl", rows, "alpaca")
        write_jsonl(cfg.OUT_DIR / f"{split}.messages.jsonl", rows, "messages")
        print(f"  写入 {split}: {len(rows)}")

    # 样例
    sample = records[0]
    with (cfg.OUT_DIR / "sample_preview.json").open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "patient_sn": sample["patient_sn"],
                "label_death": sample["label_death"],
                "input_preview": sample["input"][:800],
                "output": sample["output"],
            },
            fh,
            ensure_ascii=False,
            indent=2,
        )

    leak = audit_leakage(records)
    lengths = [r["meta"]["input_chars"] for r in records]
    summary = {
        "task": "A_death_risk_llm",
        "n_total": len(records),
        "splits": {k: len(v) for k, v in by_split.items()},
        "pos_rate": {
            k: round(float(np.mean([r["label_death"] for r in v])), 4) if v else None
            for k, v in by_split.items()
        },
        "input_chars": {
            "mean": round(float(np.mean(lengths)), 1),
            "median": round(float(np.median(lengths)), 1),
            "p90": round(float(np.quantile(lengths, 0.9)), 1),
            "max": int(np.max(lengths)),
        },
        "min_chars": cfg.MIN_CHARS,
        "max_input_chars": cfg.MAX_INPUT_CHARS,
        "formats": ["alpaca", "messages"],
        "leakage_audit": leak,
        "outputs": sorted(p.name for p in cfg.OUT_DIR.glob("*.jsonl")),
    }
    with (cfg.OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print("\n完成 LLM 数据集构建 →", cfg.OUT_DIR)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
