export const sizeData = [
  { name: '样本量', before: 78683, after: 23506 },
  { name: '列数/特征数', before: 156, after: 52 },
]

export const fillData = [
  { name: '处理前', value: 33.7 },
  { name: '处理后', value: 39.1 },
]

export const deathData = [
  { name: '存活', value: 22422 },
  { name: '死亡', value: 1084 },
]

export const genderData = [
  { name: '男', value: 18573 },
  { name: '女', value: 4933 },
]

export const cohortData = [
  { name: '强关键词可证实', value: 16100 },
  { name: '未直接坐实', value: 7406 },
]

export const moduleData = [
  { name: '人口学', fill: 80.5 },
  { name: '结局', fill: 68.2 },
  { name: '就诊', fill: 37.6 },
  { name: '入院/病史', fill: 36.2 },
  { name: '检查', fill: 36.0 },
  { name: '检验', fill: 29.7 },
  { name: '手术', fill: 12.9 },
  { name: '护理/评分', fill: 8.0 },
  { name: '病理', fill: 5.1 },
]

export const sourceData = [
  { file: '基线.csv', rows: 16823 },
  { file: '基线3', rows: 9384 },
  { file: '基线4', rows: 13774 },
  { file: '基线5', rows: 21079 },
  { file: '基线6', rows: 17623 },
]

export const splitData = [
  { set: 'train', n: 16454, pos: 4.61 },
  { set: 'val', n: 3526, pos: 4.62 },
  { set: 'test', n: 3526, pos: 4.59 },
]

export const topFeat = [
  { col: 'gender', fill: 100.0 },
  { col: 'times_of_inhospitalization', fill: 52.8 },
  { col: 'is_icu_transfer', fill: 37.6 },
  { col: 'visit_type', fill: 37.6 },
  { col: 'age', fill: 37.6 },
  { col: 'is_past_disease', fill: 37.0 },
  { col: 'is_hypertension', fill: 36.8 },
  { col: 'is_coronary', fill: 36.6 },
  { col: 'is_diabetes', fill: 36.6 },
  { col: 'is_hepatitis', fill: 36.5 },
]

export const dropped = [
  { col: 'score_grade', missing: 100.0 },
  { col: 'icu_stay_length', missing: 99.5 },
  { col: 'is_surgery_blood_transfusion', missing: 98.3 },
  { col: 'surgery_blood_loss', missing: 98.0 },
  { col: 'exam_name_2', missing: 96.0 },
  { col: 'is_menopause', missing: 95.9 },
  { col: 'is_past_tumor', missing: 95.6 },
  { col: 'is_quit_drinking', missing: 95.2 },
]

export const stats = [
  { label: '原始合计行', value: '78,683' },
  { label: '去重后患者', value: '23,506' },
  { label: '训练特征数', value: '52' },
  { label: '死亡阳性率', value: '4.61%' },
]

/** 清洗质量：患者级特征完整度分布 */
export const patientCompleteness = [
  { bucket: '0-20%', n: 14665 },
  { bucket: '20-40%', n: 2 },
  { bucket: '40-60%', n: 142 },
  { bucket: '60-80%', n: 5720 },
  { bucket: '80-100%', n: 2977 },
]

/** 清洗后特征缺失率分箱 */
export const featureMissingBuckets = [
  { bucket: '0-20%', n: 6 },
  { bucket: '20-40%', n: 2 },
  { bucket: '40-60%', n: 0 },
  { bucket: '60-80%', n: 30 },
  { bucket: '80-95%', n: 14 },
]

/** 列处置去向（清洗流水线） */
export const columnDisposition = [
  { step: '原始列', n: 156 },
  { step: 'PII 剔除', n: 7 },
  { step: 'vsn 标记剔除', n: 10 },
  { step: '文本旁路', n: 60 },
  { step: '超高缺失剔除', n: 8 },
  { step: '进入训练', n: 52 },
]

/** 字段角色构成 */
export const columnRoles = [
  { role: '文本', n: 60 },
  { role: '类别', n: 22 },
  { role: '二值', n: 19 },
  { role: '数值', n: 19 },
  { role: '日期', n: 15 },
  { role: 'vsn', n: 10 },
  { role: 'PII', n: 7 },
  { role: 'ID/标签', n: 3 },
]

/** 八维数据质量评分（0-100，基于当前清洗结果估算） */
export const qualityRadar = [
  { dim: '完整性', score: 37, fullMark: 100 },
  { dim: '唯一性', score: 95, fullMark: 100 },
  { dim: '有效性', score: 82, fullMark: 100 },
  { dim: '时效性', score: 38, fullMark: 100 },
  { dim: '一致性', score: 70, fullMark: 100 },
  { dim: '代表性', score: 69, fullMark: 100 },
  { dim: '标签质量', score: 72, fullMark: 100 },
  { dim: '可追溯性', score: 85, fullMark: 100 },
]

/** 质量总览 KPI */
export const qualityKpis = [
  { label: '综合得分', value: '68.5', tip: '八维简单平均' },
  { label: '重复行占比', value: '70.1%', tip: '去重前 55,177 / 78,683' },
  { label: '随访可算率', value: '37.6%', tip: 'follow_up_days 非空' },
  { label: '样本均完整度', value: '36.9%', tip: '训练特征非空均值' },
]

/** 各维度明细（柱状） */
export const dimensionBars = {
  completeness: [
    { name: '样本均完整度', value: 36.9 },
    { name: '完整度≥60%患者占比', value: 37.0 },
    { name: '特征缺失≤40%占比', value: 15.4 },
    { name: '人口学模块完整度', value: 80.5 },
  ],
  uniqueness: [
    { name: '去重后患者唯一', value: 100 },
    { name: '分片保留率', value: 29.9 },
    { name: '跨文件重叠剔除率', value: 70.1 },
  ],
  validity: [
    { name: 'death可映射', value: 100 },
    { name: 'gender可映射', value: 100 },
    { name: '年龄越界率(反向)', value: 100 },
    { name: '日期可解析(估)', value: 75 },
  ],
  timeliness: [
    { name: '随访可算率', value: 37.6 },
    { name: '死亡有随访占比', value: 59.0 },
    { name: '存活有随访占比', value: 36.6 },
  ],
  consistency: [
    { name: '吸烟冲突(反向)', value: 100 },
    { name: '年龄合理(反向)', value: 100 },
    { name: '死亡且可算随访', value: 59.0 },
  ],
  representativeness: [
    { name: '肝癌强关键词可证实', value: 68.5 },
    { name: '男性占比(队列特征)', value: 79.0 },
  ],
  label: [
    { name: '标签覆盖率', value: 100 },
    { name: '非极端不平衡(反向估)', value: 45 },
    { name: '死亡样本有随访', value: 59 },
  ],
  traceability: [
    { name: 'QC产物齐全', value: 90 },
    { name: '类别映射可复现', value: 85 },
    { name: '特征清单可追溯', value: 80 },
  ],
}

/** 性别 × 年龄完整度 */
export const ageCoverageByGender = [
  { gender: '女', coverage: 28.6 },
  { gender: '男', coverage: 40.0 },
]

/** 关键字段清洗前后缺失率对比 */
export const keyFieldMissing = [
  { field: 'gender', before: 0, after: 0 },
  { field: 'death', before: 0, after: 0 },
  { field: 'age', before: 62.4, after: 62.4 },
  { field: 'is_hepatitis', before: 63.5, after: 63.5 },
  { field: 'visit_type', before: 62.4, after: 62.4 },
  { field: 'follow_up_days', before: 100, after: 62.4 },
  { field: 'score_grade', before: 100, after: null },
  { field: 'icu_stay_length', before: 99.5, after: null },
]

/** 清洗步骤效果 */
export const pipelineEffect = [
  { step: '合并分片', rows: 78683, keepRate: 100 },
  { step: '患者去重', rows: 23506, keepRate: 29.9 },
  { step: '标签过滤', rows: 23506, keepRate: 29.9 },
  { step: '特征筛选', rows: 23506, keepRate: 29.9, features: 52 },
]
