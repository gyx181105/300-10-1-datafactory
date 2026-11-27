/** Task A · LLM 微调数据集（来自 dataset/task_a_llm） */

export const llmSummary = {
  task: 'A · 死亡风险 LLM',
  nTotal: 16233,
  nSkippedShort: 7273,
  nSourcePatients: 23506,
  formats: ['alpaca', 'messages'],
  minChars: 40,
  maxInputChars: 6000,
  path: 'dataset/task_a_llm/',
}

export const llmSplit = [
  { set: 'train', n: 11365, pos: 6.34 },
  { set: 'val', n: 2423, pos: 6.4 },
  { set: 'test', n: 2445, pos: 6.26 },
]

export const llmInputChars = {
  mean: 1718.8,
  median: 1723,
  p90: 3758,
  max: 5996,
}

/** train 集 input 长度分布 */
export const llmLengthHist = [
  { bucket: '<200', n: 1870 },
  { bucket: '200-500', n: 1858 },
  { bucket: '500-1k', n: 1130 },
  { bucket: '1k-2k', n: 1662 },
  { bucket: '2k-4k', n: 4008 },
  { bucket: '4k-6k', n: 837 },
]

/** train 集各病历段落覆盖人数 */
export const llmSectionCoverage = [
  { section: '基线摘要', n: 11365 },
  { section: '现病史', n: 11362 },
  { section: '诊断', n: 11359 },
  { section: '主诉', n: 6190 },
  { section: '既往史', n: 6120 },
  { section: '家族史', n: 6119 },
  { section: '个人史', n: 6103 },
  { section: '查体', n: 6075 },
  { section: '检查结论', n: 6007 },
  { section: '阳性症状', n: 5866 },
  { section: '基础病', n: 4649 },
  { section: '手术操作', n: 3299 },
]

export const llmPipeline = [
  { step: '去重患者', n: 23506 },
  { step: '有足够病历', n: 16233 },
  { step: 'LLM train', n: 11365 },
]

export const llmSamplePreview = {
  patient_sn: 'a15091e58ef24c698ea57fc39d33162f',
  label_death: 0,
  output: '0',
  input_preview:
    '【基线摘要】性别：男\n【现病史】乙肝肝癌复诊开药，患者于2026-05-07做了MR增强-DWI（加收）,上腹部MRI增强,MR增强包2,结果如下:1.肝部分切除术后改变：术区肝周少量积液，右上腹壁软组织稍肿胀。2.新增肝S8段近膈顶处结节，提示小肝Ca可能，请结合临床。3.肝内少许一过性强化结节灶，较前（2025.12.31）稍增多，异常灌注可能，随诊复查。4.残肝形态欠规整，请结合临床除外肝硬化。5.胆汁淤积；胆囊结石；胆囊炎可能。病情稳定，达到长期用药管理目标，符合长期处方管理规范要求，续方\n【诊断】肝细胞癌(CNLC IIb期)',
}
