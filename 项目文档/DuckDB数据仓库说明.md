# DuckDB 数据仓库说明

供 **大模型 Text2SQL / 工具调用** 查询肝癌死亡风险相关数据。

---

## 1. 构建仓库

首次需项目虚拟环境（系统 Anaconda 可能无写权限装 duckdb）：

```bat
cd /d d:\code\300-10-1-datafactory
python -m venv .venv
.venv\Scripts\python.exe -m pip install duckdb pandas pyarrow

.venv\Scripts\python.exe server\build_duckdb_warehouse.py
```

**产出**

| 路径 | 说明 |
|---|---|
| `warehouse/hcc_llm.duckdb` | DuckDB 库文件 |
| `warehouse/llm_sql_schema_prompt.txt` | 给大模型的表结构提示词 |
| `warehouse/summary.json` | 行数摘要 |

依赖：已生成 `dataset/task_a/`、`dataset/task_a_llm/`、`output/text_fields_sidecar.csv`。

---

## 2. 有哪些表

| 表 / 视图 | 内容 |
|---|---|
| `patients` | 患者主表（标签、split、表型） |
| `llm_samples` | LLM 样本：`instruction` / `input` / `output` |
| `clinical_text` | 病历原文旁路（已去掉死因等泄漏列） |
| `text_features` | 规则抽取开关特征 |
| `schema_catalog` | 列字典（模型可先查这个） |
| `v_patient_llm` | 患者 × LLM 样本简视图 |

关联键统一：`patient_sn`。

---

## 3. 大模型怎么查

推荐流程：

1. 把 `warehouse/llm_sql_schema_prompt.txt` 放进 system / tool 说明  
2. 模型只生成 **SELECT**  
3. 后端用只读连接执行，把结果表再喂回模型  

本地试查：

```bat
.venv\Scripts\python.exe server\query_duckdb_demo.py

.venv\Scripts\python.exe server\query_duckdb_demo.py "SELECT split, count(*) n, avg(label_death) pos FROM llm_samples GROUP BY 1"
```

Python 片段：

```python
import duckdb
con = duckdb.connect(r"d:\code\300-10-1-datafactory\warehouse\hcc_llm.duckdb", read_only=True)
print(con.execute("SELECT * FROM schema_catalog LIMIT 20").df())
```

---

## 4. 安全约定（给工具层）

- 只读打开：`read_only=True`
- 拒绝 `INSERT/UPDATE/DELETE/DROP/COPY/...`
- 表白名单：上表 + `v_patient_llm`
- 限制返回行数（如 `LIMIT 200`）与超时

---

## 5. 示例 SQL

```sql
-- 各划分样本量与阳性率
SELECT split, count(*) AS n, avg(label_death) AS pos_rate
FROM llm_samples GROUP BY 1;

-- 高风险样本的病历长度
SELECT patient_sn, input_chars
FROM llm_samples WHERE label_death = 1
ORDER BY input_chars DESC LIMIT 20;

-- 查某患者现病史（列名以实际 clinical_text 为准）
SELECT patient_sn, chief_complain, last_diagnosis
FROM clinical_text
WHERE patient_sn = '……';

-- 先看有哪些列
SELECT column_name, data_type
FROM schema_catalog
WHERE table_name = 'clinical_text';
```
