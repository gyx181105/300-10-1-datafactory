# -*- coding: utf-8 -*-
"""
将 Task A / LLM 语料 / 病历文本导入 DuckDB，供大模型 Text2SQL 查询。

输出：warehouse/hcc_llm.duckdb

用法（在项目根目录执行）：
  .venv\\Scripts\\python.exe server\\build_duckdb_warehouse.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

try:
    import duckdb
except ModuleNotFoundError as e:
    raise SystemExit(
        "未安装 duckdb。请使用项目虚拟环境：\n"
        "  .venv\\Scripts\\python.exe -m pip install duckdb pandas pyarrow\n"
        "  .venv\\Scripts\\python.exe server\\build_duckdb_warehouse.py"
    ) from e

from config import duckdb_warehouse as cfg


def _read_jsonl(path: Path) -> pd.DataFrame:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            rows.append(
                {
                    "patient_sn": o.get("patient_sn"),
                    "split": o.get("split"),
                    "label_death": o.get("label_death"),
                    "instruction": o.get("instruction"),
                    "input": o.get("input"),
                    "output": o.get("output"),
                    "input_chars": len(o.get("input") or ""),
                }
            )
    return pd.DataFrame(rows)


def _load_llm_samples() -> pd.DataFrame:
    parts = []
    for split in ("train", "val", "test"):
        p = cfg.TASK_A_LLM_DIR / f"{split}.alpaca.jsonl"
        if not p.exists():
            raise SystemExit(f"缺少 {p}，请先运行 python server\\build_llm_dataset_a.py")
        parts.append(_read_jsonl(p))
    df = pd.concat(parts, ignore_index=True)
    df["label_death"] = pd.to_numeric(df["label_death"], errors="coerce").astype("Int64")
    return df


def _load_patients() -> pd.DataFrame:
    # 优先 patients.csv；否则拼 features_*
    p = cfg.TASK_A_DIR / "patients.csv"
    if p.exists():
        df = pd.read_csv(p, dtype={"patient_sn": str}, low_memory=False)
    else:
        frames = []
        for split in ("train", "val", "test"):
            fp = cfg.TASK_A_DIR / f"features_{split}.csv"
            if fp.exists():
                t = pd.read_csv(fp, dtype={"patient_sn": str}, low_memory=False)
                if "split" not in t.columns:
                    t["split"] = split
                frames.append(t)
        if not frames:
            raise SystemExit("缺少 dataset/task_a/patients.csv 或 features_*.csv")
        df = pd.concat(frames, ignore_index=True)
    df["patient_sn"] = df["patient_sn"].astype(str)
    if "label_death" in df.columns:
        df["label_death"] = pd.to_numeric(df["label_death"], errors="coerce").astype("Int64")
    return df.drop_duplicates("patient_sn", keep="first")


def _load_clinical_text() -> pd.DataFrame:
    if not cfg.SIDECAR.exists():
        raise SystemExit(f"缺少 {cfg.SIDECAR}")
    df = pd.read_csv(cfg.SIDECAR, dtype=str, low_memory=False)
    df["patient_sn"] = df["patient_sn"].astype(str)
    drop = [c for c in df.columns if c in cfg.FORBIDDEN_TEXT_COLS]
    if drop:
        df = df.drop(columns=drop)
    return df.drop_duplicates("patient_sn", keep="first")


def _load_text_features() -> pd.DataFrame | None:
    p = cfg.TASK_A_DIR / "text_features.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p, dtype={"patient_sn": str}, low_memory=False)
    df["patient_sn"] = df["patient_sn"].astype(str)
    return df.drop_duplicates("patient_sn", keep="first")


def _schema_catalog(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    rows = []
    tables = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY 1"
    ).fetchall()
    for (tname,) in tables:
        if tname == "schema_catalog":
            continue
        cols = con.execute(
            f"SELECT column_name, data_type FROM information_schema.columns "
            f"WHERE table_schema='main' AND table_name=? ORDER BY ordinal_position",
            [tname],
        ).fetchall()
        doc = cfg.TABLE_DOCS.get(tname, "")
        for cname, dtype in cols:
            rows.append(
                {
                    "table_name": tname,
                    "column_name": cname,
                    "data_type": dtype,
                    "table_doc": doc,
                }
            )
    return pd.DataFrame(rows)


def build() -> Path:
    cfg.OUT_DIR.mkdir(parents=True, exist_ok=True)
    if cfg.DB_PATH.exists():
        cfg.DB_PATH.unlink()

    print("读取源表…")
    patients = _load_patients()
    llm = _load_llm_samples()
    clinical = _load_clinical_text()
    text_feat = _load_text_features()
    print(
        f"  patients={len(patients)} llm_samples={len(llm)} "
        f"clinical_text={len(clinical)} text_features={0 if text_feat is None else len(text_feat)}"
    )

    con = duckdb.connect(str(cfg.DB_PATH))
    try:
        con.register("patients_df", patients)
        con.execute("CREATE TABLE patients AS SELECT * FROM patients_df")
        con.unregister("patients_df")

        con.register("llm_df", llm)
        con.execute("CREATE TABLE llm_samples AS SELECT * FROM llm_df")
        con.unregister("llm_df")

        con.register("clinical_df", clinical)
        con.execute("CREATE TABLE clinical_text AS SELECT * FROM clinical_df")
        con.unregister("clinical_df")

        if text_feat is not None:
            con.register("tf_df", text_feat)
            con.execute("CREATE TABLE text_features AS SELECT * FROM tf_df")
            con.unregister("tf_df")

        # 索引友好：patient_sn 无物理索引需求，建视图方便 LLM
        con.execute(
            """
            CREATE OR REPLACE VIEW v_patient_llm AS
            SELECT
              p.patient_sn,
              p.label_death,
              coalesce(p.split, l.split) AS split,
              l.input_chars,
              l.output AS llm_output,
              length(coalesce(l.input, '')) AS has_llm_input
            FROM patients p
            LEFT JOIN llm_samples l USING (patient_sn)
            """
        )

        catalog = _schema_catalog(con)
        con.register("catalog_df", catalog)
        con.execute("CREATE TABLE schema_catalog AS SELECT * FROM catalog_df")
        con.unregister("catalog_df")

        # 写出 schema 提示文本，给大模型当 system/tool 说明
        lines = [
            "你是肝癌数据查询助手。只能对下列 DuckDB 表写只读 SQL（SELECT）。",
            f"数据库文件：{cfg.DB_PATH.as_posix()}",
            "",
        ]
        for t, doc in cfg.TABLE_DOCS.items():
            lines.append(f"## {t}\n{doc}")
            sub = catalog[catalog["table_name"] == t][["column_name", "data_type"]]
            if len(sub):
                for _, r in sub.iterrows():
                    lines.append(f"- {r['column_name']}: {r['data_type']}")
            lines.append("")
        lines.append("规则：禁止 UPDATE/DELETE/DROP；涉及死亡标签用 label_death；按患者关联键 patient_sn。")
        prompt_path = cfg.OUT_DIR / "llm_sql_schema_prompt.txt"
        prompt_path.write_text("\n".join(lines), encoding="utf-8")

        summary = {
            "db": str(cfg.DB_PATH),
            "tables": {
                "patients": len(patients),
                "llm_samples": len(llm),
                "clinical_text": len(clinical),
                "text_features": None if text_feat is None else len(text_feat),
            },
            "views": ["v_patient_llm"],
            "schema_prompt": str(prompt_path),
            "example_queries": [
                "SELECT split, count(*), avg(label_death) FROM llm_samples GROUP BY 1",
                "SELECT patient_sn, label_death, input_chars FROM llm_samples WHERE label_death=1 LIMIT 10",
                "SELECT column_name, data_type FROM schema_catalog WHERE table_name='patients'",
            ],
        }
        with (cfg.OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)

        print("\n写入", cfg.DB_PATH)
        print("schema 提示", prompt_path)
        for q in summary["example_queries"]:
            print("  试查:", q)
            print(con.execute(q).df().head(3).to_string(index=False))
            print()
    finally:
        con.close()
    return cfg.DB_PATH


if __name__ == "__main__":
    build()
