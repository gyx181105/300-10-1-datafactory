/** Task A 死亡二分类训练集与基线结果（来自 dataset/task_a，A1 文本特征版） */

export const taskASummary = {
  task: 'A · 死亡二分类（表型 + 文本规则）',
  nPatients: 23506,
  nFeatures: 85,
  positiveRate: 0.0461,
  cohortStrongN: 16051,
  cohortStrongRate: 0.683,
  labelUncertainN: 444,
  gatesPass: true,
  deathWithFollowupRate: 0.5904,
}

export const taskASplit = [
  { set: 'train', n: 16454, pos: 4.61 },
  { set: 'val', n: 3526, pos: 4.62 },
  { set: 'test', n: 3526, pos: 4.59 },
]

export const taskACoreMissing = [
  { feature: 'gender', missing: 0 },
  { feature: 'age', missing: 62.39 },
  { feature: 'is_smoking', missing: 63.1 },
  { feature: 'is_hepatitis', missing: 67.47 },
]

export const taskAGates = [
  { name: '标签可映射', pass: true, value: '100%' },
  { name: '患者唯一', pass: true, value: '通过' },
  { name: '特征数≥10', pass: true, value: '85' },
  { name: '死亡有随访', pass: false, value: '59.0%' },
]

export const baselineMetrics = [
  {
    model: 'Logistic',
    val_auroc: 0.782,
    test_auroc: 0.7638,
    val_auprc: 0.1765,
    test_auprc: 0.142,
  },
  {
    model: 'HGB',
    val_auroc: 0.7998,
    test_auroc: 0.7676,
    val_auprc: 0.1848,
    test_auprc: 0.154,
  },
]

export const baselineAurocBars = [
  { model: 'Logistic', val: 0.782, test: 0.7638 },
  { model: 'HGB', val: 0.7998, test: 0.7676 },
]

export const baselineAuprcBars = [
  { model: 'Logistic', val: 0.1765, test: 0.142 },
  { model: 'HGB', val: 0.1848, test: 0.154 },
]

export const hgbTopFeatures = [
  { feature: 'times_of_inhospitalization', importance: 0.085811 },
  { feature: 'baseline_year', importance: 0.045973 },
  { feature: 'has_ascites', importance: 0.026196 },
  { feature: 'is_diabetes', importance: 0.02103 },
  { feature: 'ethnicity', importance: 0.016384 },
  { feature: 'age', importance: 0.015314 },
  { feature: 'has_metastasis', importance: 0.013779 },
  { feature: 'has_hbv', importance: 0.007149 },
  { feature: 'stage_cnlc', importance: 0.006586 },
  { feature: 'surgery_time_length', importance: 0.006235 },
  { feature: 'symptom_jaundice', importance: 0.005755 },
  { feature: 'weight_change_value', importance: 0.003038 },
  { feature: 'cirrhosis_decompensated', importance: 0.001964 },
  { feature: 'total_score', importance: 0.001732 },
  { feature: 'is_smoking', importance: 0.001261 },
]

/** 文本规则特征阳性率（来自 text_feature_coverage.json） */
export const textFeatureCoverage = [
  { feature: 'has_hbv', pos: 35.0 },
  { feature: 'has_cirrhosis', pos: 33.7 },
  { feature: 'tx_tace', pos: 20.0 },
  { feature: 'has_ascites', pos: 13.2 },
  { feature: 'cirrhosis_decompensated', pos: 11.8 },
  { feature: 'has_metastasis', pos: 11.0 },
  { feature: 'has_stage', pos: 9.6 },
  { feature: 'symptom_jaundice', pos: 8.2 },
  { feature: 'tx_resection', pos: 7.4 },
  { feature: 'has_variceal_bleed', pos: 6.6 },
  { feature: 'tx_ablation', pos: 5.5 },
  { feature: 'has_portal_vein_thrombus', pos: 4.9 },
  { feature: 'symptom_bleed', pos: 3.5 },
  { feature: 'cirrhosis_compensated', pos: 1.4 },
  { feature: 'tx_transplant', pos: 0.8 },
]
