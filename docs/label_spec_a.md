# Task A 标签与时点说明

## 任务
基线时点死亡风险二分类。

## 标签
- 字段：`label_death`
- 映射：原始 `death` 字段，`是`→1，`否`→0
- 仅保留可映射为 0/1 的患者

## 预测时点（baseline）
- `baseline_time = visit_date`，若缺失则用 `admission_time`
- `baseline_year` 由 baseline_time 衍生
- `age`：优先用记录年龄；缺失则用 `baseline_time - birth_date`

## 随访（不作为默认分类特征）
- `follow_up_days = end_time - baseline_time`
- `end_time = death_time`，若缺失则用 `death_or_last_visit_date`
- 负值置空
- **注意**：分类主模型默认不使用 `follow_up_days`，避免间接泄漏；留给 Task B 生存分析

## 队列标记
- `cohort_hcc_strong=1`：诊断相关文本命中肝癌强关键词  
  （肝癌 / 肝细胞癌 / 原发性肝癌 / 肝恶性肿瘤 / HCC 等）
- 全队列训练为默认；可用该标记做敏感分析子集

## 质量标记
- `label_uncertain=1`：死亡=1 但无法计算随访天数
- `qc_age_oob`：年龄越界
- `qc_smoke_conflict`：声称不吸烟但烟龄>0
- `qc_death_no_followup`：同 label_uncertain

## 划分
- 按 `patient_sn` 分层划分 train/val/test ≈ 70/15/15
- `seed=42`
