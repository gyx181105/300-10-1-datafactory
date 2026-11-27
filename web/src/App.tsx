import {
  Activity,
  ArrowUpRight,
  Bell,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Download,
  FlaskConical,
  LayoutDashboard,
  MessageSquareText,
  Search,
  Settings,
  Sparkles,
  Table2,
  Users,
  XCircle,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { PieOuterLabel, RightNumLabel, RightPctLabel, TopNumLabel } from '@/components/chart-labels'
import { ChartPatterns } from '@/components/svg-patterns'
import { Button } from '@/components/ui/button'
import { Card, CardDesc, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { applyPalette, PALETTES, type PaletteId } from '@/lib/palette'
import {
  ageCoverageByGender,
  cohortData,
  columnDisposition,
  columnRoles,
  deathData,
  dimensionBars,
  dropped,
  featureMissingBuckets,
  fillData,
  genderData,
  keyFieldMissing,
  moduleData,
  patientCompleteness,
  pipelineEffect,
  qualityKpis,
  qualityRadar,
  sizeData,
  sourceData,
  splitData,
  topFeat,
} from '@/lib/qc-data'
import {
  baselineAuprcBars,
  baselineAurocBars,
  baselineMetrics,
  hgbTopFeatures,
  taskACoreMissing,
  taskAGates,
  taskASplit,
  taskASummary,
  textFeatureCoverage,
} from '@/lib/task-a-data'
import {
  llmInputChars,
  llmLengthHist,
  llmPipeline,
  llmSamplePreview,
  llmSectionCoverage,
  llmSplit,
  llmSummary,
} from '@/lib/task-a-llm-data'
import { cn } from '@/lib/utils'

const axisTick = { fill: '#8a8a8a', fontSize: 11 }

function ChartTip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{ name?: string; value?: number | string; dataKey?: string }>
  label?: string | number
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl bg-[#1a1a1a] px-3 py-2 text-[11px] text-white shadow-lg">
      <div className="mb-1 opacity-60">{label}</div>
      {payload.map((p) => (
        <div key={String(p.dataKey ?? p.name)}>
          {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
        </div>
      ))}
    </div>
  )
}

const navMain = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'llm', label: 'LLM Dataset', icon: MessageSquareText },
  { id: 'training', label: 'Tabular A', icon: FlaskConical },
  { id: 'cohort', label: 'Cohort', icon: Users },
  { id: 'modules', label: 'Modules', icon: Activity },
  { id: 'features', label: 'Features', icon: Table2 },
]

const actions = [
  { tone: '#3b82f6', title: '微调 LLM', desc: '用 dataset/task_a_llm/*.jsonl 做 SFT/LoRA' },
  { tone: '#f59e0b', title: '处理类别不平衡', desc: 'LLM 集阳性约 6.3%，需加权或重采样' },
  { tone: '#ef4444', title: '补短文本样本', desc: '约 7.3k 人因病历过短未入 LLM 集' },
  { tone: '#a3a3a3', title: '表格基线对照', desc: 'dataset/task_a 仍可用于树模型对照' },
]

export default function App() {
  const [paletteId, setPaletteId] = useState<PaletteId>('01')
  const [nav, setNav] = useState('overview')
  const palette = useMemo(
    () => PALETTES.find((p) => p.id === paletteId) ?? PALETTES[0],
    [paletteId],
  )

  useEffect(() => {
    applyPalette(palette)
  }, [palette])

  const high = palette.high
  const low = palette.low

  const waterfall = [
    { name: '原始合计', value: 78683, fill: low },
    { name: '去重移除', value: -55177, fill: high },
    { name: '有效患者', value: 23506, fill: low },
  ]

  return (
    <div className="flex min-h-screen bg-[var(--color-canvas)] text-[var(--color-ink)]">
      <ChartPatterns high={high} low={low} />

      {/* Sidebar — margin 风格 */}
      <aside className="sticky top-0 flex h-screen w-[232px] shrink-0 flex-col border-r border-[var(--color-line)] bg-[#fafafa] px-3 py-4">
        <div className="mb-4 flex items-center gap-2 px-2">
          <span
            className="grid h-7 w-7 place-items-center rounded-lg text-white"
            style={{ background: `linear-gradient(135deg, ${high}, ${low})` }}
          >
            <Sparkles size={14} />
          </span>
          <div className="leading-tight">
            <div className="text-[15px] font-semibold">hcc.qc</div>
            <div className="text-[10px] text-[var(--color-muted)]">baseline clean</div>
          </div>
        </div>

        <div className="mb-4 flex items-center gap-2 rounded-xl bg-[#efefef] px-3 py-2 text-xs text-[var(--color-muted)]">
          <Search size={14} />
          <span className="flex-1">Search</span>
          <kbd className="rounded-md bg-white px-1.5 py-0.5 text-[10px] text-[#737373]">⌘K</kbd>
        </div>

        <div className="mb-1 px-2 text-[10px] font-medium uppercase tracking-wide text-[#a3a3a3]">
          Main
        </div>
        <nav className="flex flex-col gap-0.5">
          {navMain.map((item) => {
            const Icon = item.icon
            const active = nav === item.id
            return (
              <button
                key={item.id}
                onClick={() => {
                  setNav(item.id)
                  const el = document.getElementById(
                    item.id === 'training' ? 'task-a' : item.id === 'llm' ? 'task-a-llm' : item.id,
                  )
                  el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                }}
                className={cn(
                  'flex items-center gap-2 rounded-xl px-2.5 py-2 text-left text-[13px]',
                  active ? 'bg-[#1a1a1a] text-white' : 'text-[#525252] hover:bg-black/5',
                )}
              >
                <Icon size={15} />
                {item.label}
              </button>
            )
          })}
        </nav>

        <div className="mt-5 mb-1 px-2 text-[10px] font-medium uppercase tracking-wide text-[#a3a3a3]">
          Palette
        </div>
        <div className="flex flex-col gap-1 px-1">
          {PALETTES.map((p) => (
            <button
              key={p.id}
              onClick={() => setPaletteId(p.id)}
              className={cn(
                'flex items-center gap-2 rounded-xl px-2 py-1.5 text-left text-[12px]',
                paletteId === p.id ? 'bg-white shadow-sm' : 'hover:bg-black/5',
              )}
            >
              <span className="flex h-3.5 w-7 overflow-hidden rounded-full">
                <span className="w-1/2" style={{ background: p.high }} />
                <span className="w-1/2" style={{ background: p.low }} />
              </span>
              <span className="text-[var(--color-muted)]">{p.id}</span>
            </button>
          ))}
        </div>

        <div className="mt-auto space-y-1 border-t border-[var(--color-line)] pt-3">
          <button className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-[13px] text-[#525252] hover:bg-black/5">
            <Bell size={15} />
            Alerts
            <span className="ml-auto rounded-full px-1.5 text-[10px] text-white" style={{ background: high }}>
              3
            </span>
          </button>
          <button className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-[13px] text-[#525252] hover:bg-black/5">
            <Settings size={15} />
            Settings
          </button>
          <button className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-[13px] text-[#525252] hover:bg-black/5">
            <CircleHelp size={15} />
            Help
          </button>
          <div className="mt-2 flex items-center gap-2 rounded-xl px-2 py-2">
            <div
              className="grid h-8 w-8 place-items-center rounded-full text-xs font-semibold text-white"
              style={{ background: low }}
            >
              QC
            </div>
            <div className="min-w-0 leading-tight">
              <div className="truncate text-[12px] font-medium">数据清洗</div>
              <div className="truncate text-[10px] text-[var(--color-muted)]">肝癌基线队列</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="min-w-0 flex-1 px-5 py-4 lg:px-7">
        <div id="overview" className="mb-4 flex scroll-mt-4 flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="m-0 text-[34px] font-semibold tracking-tight">Overview</h1>
            <p className="mt-1 text-[13px] text-[var(--color-muted)]">
              基线分片合并清洗 · 当前配色 {palette.name}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="soft" size="sm">
              全部患者 · 23,506
            </Button>
            <Button variant="soft" size="sm">
              death 标签
            </Button>
            <Button size="sm" className="gap-1.5">
              <Download size={14} />
              Export
            </Button>
          </div>
        </div>

        {/* Top row — 对标 margin 首屏 */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
          <Card className="xl:col-span-3">
            <CardTitle>Death rate</CardTitle>
            <CardDesc>处理后标签阳性率</CardDesc>
            <div className="mt-4 text-[42px] font-semibold leading-none tracking-tight">4.61%</div>
            <div className="mt-4">
              <div className="mb-1 flex justify-between text-[11px] text-[var(--color-muted)]">
                <span>0%</span>
                <span>目标观察 10%</span>
              </div>
              <div className="relative h-2.5 rounded-full bg-[#efefef]">
                <div
                  className="absolute inset-y-0 left-0 rounded-full"
                  style={{ width: '46.1%', background: low }}
                />
                <div className="absolute top-1/2 h-3 w-0.5 -translate-y-1/2 bg-[#1a1a1a]" style={{ left: '46.1%' }} />
              </div>
            </div>
            <div className="mt-5 space-y-2 text-[13px]">
              <div className="flex items-center justify-between">
                <span className="text-[var(--color-muted)]">存活</span>
                <span className="inline-flex items-center gap-1 font-medium">
                  22,422
                  <ArrowUpRight size={13} className="text-emerald-500" />
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[var(--color-muted)]">死亡</span>
                <span className="font-medium">1,084</span>
              </div>
              <div className="flex items-center justify-between border-t border-[var(--color-line)] pt-2">
                <span className="text-[var(--color-muted)]">整体非空率</span>
                <span className="font-medium">33.7% → 39.1%</span>
              </div>
            </div>
          </Card>

          <Card className="xl:col-span-5">
            <CardTitle>Why rows dropped</CardTitle>
            <CardDesc>从分片合计到去重患者的变化</CardDesc>
            <div className="mt-3 h-[240px]">
              <ResponsiveContainer>
                <BarChart
                  data={waterfall}
                  layout="vertical"
                  margin={{ top: 8, right: 72, left: 8, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                  <XAxis type="number" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={72}
                    tick={axisTick}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="value" name="人数变化" radius={[0, 8, 8, 0]} barSize={22} label={<TopNumLabel />}>
                    {waterfall.map((d) => (
                      <Cell key={d.name} fill={d.value < 0 ? 'url(#hatchHigh)' : 'url(#hatchLow)'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-1 grid grid-cols-3 gap-2 text-[12px]">
              <div>
                <div className="text-[var(--color-muted)]">原始行</div>
                <div className="font-semibold">78,683</div>
              </div>
              <div>
                <div className="text-[var(--color-muted)]">重复移除</div>
                <div className="font-semibold" style={{ color: high }}>
                  -55,177
                </div>
              </div>
              <div>
                <div className="text-[var(--color-muted)]">有效患者</div>
                <div className="font-semibold">23,506</div>
              </div>
            </div>
          </Card>

          <div className="grid gap-4 xl:col-span-4">
            <Card
              className="relative overflow-hidden text-white"
              style={{
                background: `linear-gradient(160deg, ${low} 0%, ${high} 100%)`,
                boxShadow: 'none',
              }}
            >
              <div className="relative z-10">
                <div className="text-[13px] font-medium opacity-90">Insight</div>
                <div className="mt-3 text-[40px] font-semibold leading-none">68.5%</div>
                <div className="mt-2 max-w-[220px] text-[13px] opacity-90">
                  诊断字段出现肝癌强关键词的患者占比
                </div>
                <div className="mt-4 text-[12px] opacity-80">16,100 / 23,506</div>
              </div>
              <div className="pointer-events-none absolute -bottom-6 -right-4 h-36 w-36 rounded-full border-[14px] border-white/25" />
              <div className="pointer-events-none absolute -bottom-2 right-10 h-20 w-20 rounded-full bg-white/15" />
            </Card>

            <Card className="p-4">
              <CardTitle className="text-[14px]">Needs you</CardTitle>
              <div className="mt-2 divide-y divide-[var(--color-line)]">
                {actions.map((a) => (
                  <button
                    key={a.title}
                    className="flex w-full items-center gap-3 py-2.5 text-left hover:opacity-80"
                  >
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: a.tone }} />
                    <span className="min-w-0 flex-1">
                      <span className="block text-[13px] font-medium">{a.title}</span>
                      <span className="block truncate text-[11px] text-[var(--color-muted)]">
                        {a.desc}
                      </span>
                    </span>
                    <ChevronRight size={14} className="text-[#a3a3a3]" />
                  </button>
                ))}
              </div>
            </Card>
          </div>
        </div>

        {/* Task A · LLM 微调数据集（主路径） */}
        <div id="task-a-llm" className="mt-6 mb-2 scroll-mt-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="m-0 text-[22px] font-semibold tracking-tight">Task A · LLM Dataset</h2>
              <p className="mt-1 text-[13px] text-[var(--color-muted)]">
                病历原文 → 死亡风险 0/1 · JSONL 微调语料 · {llmSummary.path}
              </p>
            </div>
            <span
              className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium text-white"
              style={{ background: low }}
            >
              <MessageSquareText size={14} />
              {llmSummary.formats.join(' + ')}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {[
            { label: 'LLM 样本', value: llmSummary.nTotal.toLocaleString() },
            { label: '训练集', value: llmSplit[0].n.toLocaleString() },
            { label: 'train 阳性率', value: `${llmSplit[0].pos}%` },
            { label: '中位 input 字数', value: String(llmInputChars.median) },
          ].map((k) => (
            <Card key={k.label} className="p-4">
              <div className="text-[12px] text-[var(--color-muted)]">{k.label}</div>
              <div className="mt-1 text-[26px] font-semibold tracking-tight">{k.value}</div>
            </Card>
          ))}
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-12">
          <Card className="xl:col-span-4">
            <CardTitle>样本漏斗</CardTitle>
            <CardDesc>去重患者 → 足够病历 → train</CardDesc>
            <div className="mt-2 h-[230px]">
              <ResponsiveContainer>
                <BarChart data={llmPipeline} barCategoryGap="40%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="step" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis tick={axisTick} axisLine={false} tickLine={false} width={44} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="n" name="人数" fill={low} radius={[8, 8, 0, 0]} barSize={22} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-1 text-[12px] text-[var(--color-muted)]">
              文本过短跳过 {llmSummary.nSkippedShort.toLocaleString()} 人（&lt; {llmSummary.minChars} 字）
            </div>
          </Card>

          <Card className="xl:col-span-4">
            <CardTitle>划分与阳性率</CardTitle>
            <CardDesc>与患者级 split 对齐 · 防泄漏</CardDesc>
            <div className="mt-2 h-[210px]">
              <ResponsiveContainer>
                <BarChart data={llmSplit} barCategoryGap="40%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="set" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis tick={axisTick} axisLine={false} tickLine={false} width={40} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="n" name="样本数" fill={low} radius={[8, 8, 0, 0]} barSize={20} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {llmSplit.map((s) => (
                <div key={s.set} className="rounded-xl bg-[#f7f7f7] px-2.5 py-2">
                  <div className="text-[10px] text-[var(--color-muted)]">{s.set}</div>
                  <div className="text-[14px] font-semibold">{s.n.toLocaleString()}</div>
                  <div className="text-[10px] text-[var(--color-muted)]">pos {s.pos}%</div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="xl:col-span-4">
            <CardTitle>input 长度分布</CardTitle>
            <CardDesc>
              train · 上限 {llmSummary.maxInputChars} 字 · p90={llmInputChars.p90}
            </CardDesc>
            <div className="mt-2 h-[250px]">
              <ResponsiveContainer>
                <BarChart data={llmLengthHist} barCategoryGap="28%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="bucket" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis tick={axisTick} axisLine={false} tickLine={false} width={40} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="n" name="条数" fill="url(#hatchLow)" radius={[8, 8, 0, 0]} barSize={18} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-12">
          <Card className="xl:col-span-7">
            <CardTitle>病历段落覆盖（train）</CardTitle>
            <CardDesc>JSONL input 中出现各【段落】的样本数</CardDesc>
            <div className="mt-2 h-[320px]">
              <ResponsiveContainer>
                <BarChart
                  data={[...llmSectionCoverage].reverse()}
                  layout="vertical"
                  margin={{ top: 4, right: 36, left: 4, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                  <XAxis type="number" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis
                    type="category"
                    dataKey="section"
                    width={72}
                    tick={{ fill: '#8a8a8a', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="n" name="覆盖" fill={low} radius={[0, 8, 8, 0]} barSize={12} label={<RightNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="xl:col-span-5">
            <CardTitle>样本预览</CardTitle>
            <CardDesc>
              {llmSamplePreview.patient_sn.slice(0, 8)}… · label={llmSamplePreview.label_death} ·
              output=&quot;{llmSamplePreview.output}&quot;
            </CardDesc>
            <pre className="mt-3 max-h-[300px] overflow-auto rounded-xl bg-[#f7f7f7] p-3 text-[11px] leading-relaxed whitespace-pre-wrap text-[#404040]">
              {llmSamplePreview.input_preview}
            </pre>
            <div className="mt-3 grid grid-cols-2 gap-2 text-[12px]">
              <div className="rounded-xl bg-[#f7f7f7] px-3 py-2">
                <div className="text-[10px] text-[var(--color-muted)]">均值字数</div>
                <div className="text-[16px] font-semibold">{llmInputChars.mean}</div>
              </div>
              <div className="rounded-xl bg-[#f7f7f7] px-3 py-2">
                <div className="text-[10px] text-[var(--color-muted)]">最大字数</div>
                <div className="text-[16px] font-semibold">{llmInputChars.max}</div>
              </div>
            </div>
          </Card>
        </div>

        {/* Task A 表格对照（旧路径） */}
        <div id="task-a" className="mt-10 mb-2 scroll-mt-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="m-0 text-[22px] font-semibold tracking-tight">Task A · Tabular（对照）</h2>
              <p className="mt-1 text-[13px] text-[var(--color-muted)]">
                数值特征 + 规则抽取 · 非 LLM 主路径 · dataset/task_a
              </p>
            </div>
            <span
              className={cn(
                'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium text-white',
              )}
              style={{ background: taskASummary.gatesPass ? low : high }}
            >
              {taskASummary.gatesPass ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
              门禁 {taskASummary.gatesPass ? '通过' : '未通过'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {[
            { label: '训练患者', value: taskASummary.nPatients.toLocaleString() },
            { label: '建模特征', value: String(taskASummary.nFeatures) },
            { label: '阳性率', value: `${(taskASummary.positiveRate * 100).toFixed(2)}%` },
            { label: '肝癌可证实', value: `${(taskASummary.cohortStrongRate * 100).toFixed(1)}%` },
          ].map((k) => (
            <Card key={k.label} className="p-4">
              <div className="text-[12px] text-[var(--color-muted)]">{k.label}</div>
              <div className="mt-1 text-[26px] font-semibold tracking-tight">{k.value}</div>
            </Card>
          ))}
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-12">
          <Card className="xl:col-span-4">
            <CardTitle>数据划分</CardTitle>
            <CardDesc>分层 70 / 15 / 15 · seed=42</CardDesc>
            <div className="mt-2 h-[210px]">
              <ResponsiveContainer>
                <BarChart data={taskASplit} barCategoryGap="40%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="set" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis tick={axisTick} axisLine={false} tickLine={false} width={40} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="n" name="样本数" fill={low} radius={[8, 8, 0, 0]} barSize={20} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {taskASplit.map((s) => (
                <div key={s.set} className="rounded-xl bg-[#f7f7f7] px-2.5 py-2">
                  <div className="text-[10px] text-[var(--color-muted)]">{s.set}</div>
                  <div className="text-[14px] font-semibold">{s.n.toLocaleString()}</div>
                  <div className="text-[10px] text-[var(--color-muted)]">pos {s.pos}%</div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="xl:col-span-4">
            <CardTitle>基线 AUROC</CardTitle>
            <CardDesc>Logistic vs HistGradientBoosting</CardDesc>
            <div className="mt-2 h-[250px]">
              <ResponsiveContainer>
                <BarChart data={baselineAurocBars} barGap={6} barCategoryGap="35%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="model" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis domain={[0.5, 1]} tick={axisTick} axisLine={false} tickLine={false} width={36} />
                  <Tooltip content={<ChartTip />} />
                  <Legend />
                  <Bar dataKey="val" name="val" fill="url(#hatchLow)" radius={[8, 8, 0, 0]} barSize={16} label={<TopNumLabel />} />
                  <Bar dataKey="test" name="test" fill={low} radius={[8, 8, 0, 0]} barSize={16} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="xl:col-span-4">
            <CardTitle>基线 AUPRC</CardTitle>
            <CardDesc>阳性率仅 4.6%，AUPRC 更敏感</CardDesc>
            <div className="mt-2 h-[250px]">
              <ResponsiveContainer>
                <BarChart data={baselineAuprcBars} barGap={6} barCategoryGap="35%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="model" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 0.25]} tick={axisTick} axisLine={false} tickLine={false} width={36} />
                  <Tooltip content={<ChartTip />} />
                  <Legend />
                  <Bar dataKey="val" name="val" fill="url(#hatchHigh)" radius={[8, 8, 0, 0]} barSize={16} label={<TopNumLabel />} />
                  <Bar dataKey="test" name="test" fill={high} radius={[8, 8, 0, 0]} barSize={16} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-12">
          <Card className="xl:col-span-5">
            <CardTitle>HGB 重要特征（置换 AUPRC）</CardTitle>
            <CardDesc>val 子集 permutation importance Top</CardDesc>
            <div className="mt-2 h-[320px]">
              <ResponsiveContainer>
                <BarChart
                  data={[...hgbTopFeatures].reverse()}
                  layout="vertical"
                  margin={{ top: 4, right: 28, left: 4, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                  <XAxis type="number" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis
                    type="category"
                    dataKey="feature"
                    width={150}
                    tick={{ fill: '#8a8a8a', fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="importance" name="importance" fill={low} radius={[0, 8, 8, 0]} barSize={12} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="xl:col-span-3">
            <CardTitle>门禁检查</CardTitle>
            <CardDesc>训练前质量门槛</CardDesc>
            <div className="mt-3 space-y-2">
              {taskAGates.map((g) => (
                <div
                  key={g.name}
                  className="flex items-center justify-between rounded-xl bg-[#f7f7f7] px-3 py-2.5"
                >
                  <div className="flex items-center gap-2 text-[13px]">
                    {g.pass ? (
                      <CheckCircle2 size={15} style={{ color: low }} />
                    ) : (
                      <XCircle size={15} style={{ color: high }} />
                    )}
                    {g.name}
                  </div>
                  <div className="text-[12px] font-medium text-[var(--color-muted)]">{g.value}</div>
                </div>
              ))}
            </div>
            <div className="mt-3 rounded-xl px-3 py-2 text-[12px] text-[var(--color-muted)]" style={{ background: `${low}14` }}>
              不确定标签（死亡无随访）：{taskASummary.labelUncertainN} 人
            </div>
          </Card>

          <Card className="xl:col-span-4">
            <CardTitle>核心特征缺失率</CardTitle>
            <CardDesc>仍需优先回填的字段</CardDesc>
            <div className="mt-2 h-[220px]">
              <ResponsiveContainer>
                <BarChart data={taskACoreMissing} layout="vertical" margin={{ top: 4, right: 36, left: 4, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} unit="%" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="feature" width={88} tick={axisTick} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="missing" name="缺失%" fill="url(#hatchHigh)" radius={[0, 8, 8, 0]} barSize={14} label={<RightPctLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 overflow-hidden rounded-xl border border-[var(--color-line)]">
              <table className="w-full border-collapse text-[12px]">
                <thead>
                  <tr className="bg-[#f7f7f7] text-[var(--color-muted)]">
                    <th className="px-3 py-2 text-left font-medium">模型</th>
                    <th className="px-3 py-2 text-right font-medium">val AUC</th>
                    <th className="px-3 py-2 text-right font-medium">test AUC</th>
                  </tr>
                </thead>
                <tbody>
                  {baselineMetrics.map((m) => (
                    <tr key={m.model} className="border-t border-[var(--color-line)]">
                      <td className="px-3 py-2">{m.model}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{m.val_auroc}</td>
                      <td className="px-3 py-2 text-right tabular-nums font-semibold">{m.test_auroc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        <div className="mt-4">
          <Card>
            <CardTitle>文本规则特征 · 阳性率</CardTitle>
            <CardDesc>A1 从诊断/病史抽取 · 来源 text_feature_coverage.json</CardDesc>
            <div className="mt-2 h-[280px]">
              <ResponsiveContainer>
                <BarChart
                  data={textFeatureCoverage}
                  margin={{ top: 22, right: 8, left: 0, bottom: 48 }}
                  barCategoryGap="28%"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis
                    dataKey="feature"
                    tick={{ fill: '#8a8a8a', fontSize: 9 }}
                    axisLine={false}
                    tickLine={false}
                    interval={0}
                    angle={-35}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis unit="%" tick={axisTick} axisLine={false} tickLine={false} width={36} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="pos" name="阳性%" fill={low} radius={[8, 8, 0, 0]} barSize={14} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* Second row */}
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardTitle>样本量与维度</CardTitle>
            <CardDesc>处理前合计行 vs 去重后患者；列数压缩到训练特征</CardDesc>
            <div className="mt-2 h-[250px]">
              <ResponsiveContainer>
                <BarChart data={sizeData} barGap={6} barCategoryGap="40%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="name" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis tick={axisTick} axisLine={false} tickLine={false} width={44} />
                  <Tooltip content={<ChartTip />} />
                  <Legend />
                  <Bar dataKey="before" name="处理前" fill="url(#hatchHigh)" radius={[8, 8, 0, 0]} barSize={18} label={<TopNumLabel />} />
                  <Bar dataKey="after" name="处理后" fill={low} radius={[8, 8, 0, 0]} barSize={18} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <CardTitle>分片行数</CardTitle>
            <CardDesc>去重前各 CSV 行数 · Target 为去重后患者数</CardDesc>
            <div className="mt-2 h-[250px]">
              <ResponsiveContainer>
                <BarChart data={sourceData} barCategoryGap="35%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="file" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis tick={axisTick} axisLine={false} tickLine={false} width={44} />
                  <Tooltip content={<ChartTip />} />
                  <ReferenceLine y={23506} stroke="#1a1a1a" strokeDasharray="4 4" label={{ value: 'Dedup 23,506', position: 'insideTopRight', fill: '#737373', fontSize: 11 }} />
                  <Bar dataKey="rows" name="行数" fill="url(#hatchLow)" radius={[8, 8, 0, 0]} barSize={18} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
          <Card>
            <CardTitle>分布</CardTitle>
            <CardDesc>点击切换标签 / 性别 / 可证实性</CardDesc>
            <Tabs defaultValue="death" className="mt-2">
              <TabsList className="border-none bg-[#f3f3f3] p-1 rounded-xl">
                <TabsTrigger value="death" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">
                  死亡
                </TabsTrigger>
                <TabsTrigger value="gender" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">
                  性别
                </TabsTrigger>
                <TabsTrigger value="cohort" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">
                  可证实
                </TabsTrigger>
              </TabsList>
              {[
                { key: 'death', data: deathData },
                { key: 'gender', data: genderData },
                { key: 'cohort', data: cohortData },
              ].map((tab) => (
                <TabsContent key={tab.key} value={tab.key}>
                  <div className="h-[250px]">
                    <ResponsiveContainer>
                      <PieChart margin={{ top: 8, right: 12, bottom: 8, left: 12 }}>
                        <Pie
                          data={tab.data}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="48%"
                          innerRadius={48}
                          outerRadius={72}
                          paddingAngle={3}
                          label={PieOuterLabel}
                          labelLine={false}
                        >
                          {tab.data.map((entry, i) => (
                            <Cell key={entry.name} fill={i === 0 ? low : high} />
                          ))}
                        </Pie>
                        <Tooltip content={<ChartTip />} />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </Card>

          <Card>
            <CardTitle>模块完整度</CardTitle>
            <CardDesc>处理前各业务模块字段平均非空率</CardDesc>
            <div className="mt-2 h-[290px]">
              <ResponsiveContainer>
                <BarChart data={moduleData} layout="vertical" margin={{ top: 4, right: 36, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} unit="%" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" width={68} tick={axisTick} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="fill" name="非空率" fill={low} radius={[0, 8, 8, 0]} barSize={14} label={<RightPctLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <CardTitle>字段完整度对比</CardTitle>
            <CardDesc>清洗前后整体非空率</CardDesc>
            <div className="mt-2 h-[290px]">
              <ResponsiveContainer>
                <BarChart data={fillData} layout="vertical" margin={{ top: 8, right: 40, left: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} unit="%" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" width={52} tick={axisTick} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="value" name="非空率" radius={[0, 8, 8, 0]} barSize={22} label={<RightPctLabel />}>
                    {fillData.map((d, i) => (
                      <Cell key={d.name} fill={i === 0 ? 'url(#hatchHigh)' : low} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardTitle>分层划分</CardTitle>
            <CardDesc>train / val / test = 70 / 15 / 15</CardDesc>
            <div className="mt-2 h-[210px]">
              <ResponsiveContainer>
                <BarChart data={splitData} barCategoryGap="45%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="set" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis tick={axisTick} axisLine={false} tickLine={false} width={44} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="n" name="样本数" fill={low} radius={[8, 8, 0, 0]} barSize={20} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {splitData.map((s) => (
                <div key={s.set} className="rounded-xl bg-[#f7f7f7] px-3 py-2">
                  <div className="text-[11px] text-[var(--color-muted)]">{s.set}</div>
                  <div className="text-[15px] font-semibold">{s.n.toLocaleString()}</div>
                  <div className="text-[11px] text-[var(--color-muted)]">{s.pos.toFixed(2)}%</div>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <CardTitle>填充率 Top</CardTitle>
                <CardDesc>训练特征非空率</CardDesc>
                <div className="mt-2 h-[280px]">
                  <ResponsiveContainer>
                    <BarChart data={[...topFeat].reverse()} layout="vertical" margin={{ top: 0, right: 34, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                      <XAxis type="number" domain={[0, 100]} tick={axisTick} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="col" width={110} tick={{ fill: '#8a8a8a', fontSize: 10 }} axisLine={false} tickLine={false} />
                      <Tooltip content={<ChartTip />} />
                      <Bar dataKey="fill" name="非空率" fill={low} radius={[0, 6, 6, 0]} barSize={10} label={<RightPctLabel />} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div>
                <CardTitle>高缺失剔除</CardTitle>
                <CardDesc>缺失率 &gt; 95%</CardDesc>
                <div className="mt-2 h-[280px]">
                  <ResponsiveContainer>
                    <BarChart data={[...dropped].reverse()} layout="vertical" margin={{ top: 0, right: 34, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                      <XAxis type="number" domain={[90, 100]} tick={axisTick} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="col" width={120} tick={{ fill: '#8a8a8a', fontSize: 10 }} axisLine={false} tickLine={false} />
                      <Tooltip content={<ChartTip />} />
                      <Bar dataKey="missing" name="缺失率" fill="url(#hatchHigh)" radius={[0, 6, 6, 0]} barSize={10} label={<RightPctLabel />} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* 数据质量八维 */}
        <div className="mt-6 mb-2">
          <h2 className="m-0 text-[22px] font-semibold tracking-tight">Data quality</h2>
          <p className="mt-1 text-[13px] text-[var(--color-muted)]">
            雷达看总览，柱状看各维度明细；得分基于当前清洗结果估算（0–100）
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {qualityKpis.map((k) => (
            <Card key={k.label} className="p-4">
              <div className="text-[12px] text-[var(--color-muted)]">{k.label}</div>
              <div className="mt-1 text-[28px] font-semibold tracking-tight">{k.value}</div>
              <div className="mt-1 text-[11px] text-[var(--color-muted)]">{k.tip}</div>
            </Card>
          ))}
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-12">
          <Card className="xl:col-span-5">
            <CardTitle>质量维度雷达图</CardTitle>
            <CardDesc>完整性 / 唯一性 / 有效性 / 时效性 / 一致性 / 代表性 / 标签 / 可追溯性</CardDesc>
            <div className="mt-2 h-[340px]">
              <ResponsiveContainer>
                <RadarChart data={qualityRadar} cx="50%" cy="50%" outerRadius="72%">
                  <PolarGrid stroke="#e5e5e5" />
                  <PolarAngleAxis dataKey="dim" tick={{ fill: '#737373', fontSize: 11 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#a3a3a3', fontSize: 10 }} />
                  <Radar
                    name="得分"
                    dataKey="score"
                    stroke={low}
                    fill={low}
                    fillOpacity={0.28}
                    strokeWidth={2}
                  />
                  <Tooltip content={<ChartTip />} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-1 grid grid-cols-4 gap-2">
              {qualityRadar.map((d) => (
                <div key={d.dim} className="rounded-xl bg-[#f7f7f7] px-2 py-1.5 text-center">
                  <div className="text-[10px] text-[var(--color-muted)]">{d.dim}</div>
                  <div className="text-[14px] font-semibold" style={{ color: d.score < 50 ? high : low }}>
                    {d.score}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="xl:col-span-7">
            <CardTitle>各维度得分对比</CardTitle>
            <CardDesc>同一套八维分数的柱状对照，便于看短板</CardDesc>
            <div className="mt-2 h-[340px]">
              <ResponsiveContainer>
                <BarChart data={qualityRadar} layout="vertical" margin={{ top: 4, right: 36, left: 4, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="dim" width={64} tick={axisTick} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTip />} />
                  <ReferenceLine x={60} stroke="#a3a3a3" strokeDasharray="4 4" />
                  <Bar dataKey="score" name="得分" radius={[0, 8, 8, 0]} barSize={16} label={<RightNumLabel />}>
                    {qualityRadar.map((d) => (
                      <Cell key={d.dim} fill={d.score < 60 ? 'url(#hatchHigh)' : low} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-1 text-[11px] text-[var(--color-muted)]">虚线为及格参考线 60 分；低于 60 用斜线填充高亮。</p>
          </Card>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardTitle>完整性 · 明细</CardTitle>
            <CardDesc>样本/特征/模块完整度指标（%）</CardDesc>
            <div className="mt-2 h-[240px]">
              <ResponsiveContainer>
                <BarChart data={dimensionBars.completeness} layout="vertical" margin={{ top: 4, right: 36, left: 4, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" width={130} tick={{ fill: '#8a8a8a', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="value" name="%" fill={low} radius={[0, 8, 8, 0]} barSize={14} label={<RightPctLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <CardTitle>完整性 · 患者完整度分布</CardTitle>
            <CardDesc>训练特征非空比例分箱 · 中位数约 15%</CardDesc>
            <div className="mt-2 h-[240px]">
              <ResponsiveContainer>
                <BarChart data={patientCompleteness} barCategoryGap="30%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="bucket" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis tick={axisTick} axisLine={false} tickLine={false} width={44} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="n" name="患者数" fill="url(#hatchLow)" radius={[8, 8, 0, 0]} barSize={22} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <CardTitle>唯一性 / 流水线</CardTitle>
            <CardDesc>去重效果与保留率</CardDesc>
            <div className="mt-2 h-[200px]">
              <ResponsiveContainer>
                <BarChart data={dimensionBars.uniqueness} barCategoryGap="35%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: '#8a8a8a', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={axisTick} axisLine={false} tickLine={false} width={32} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="value" name="%" fill={low} radius={[8, 8, 0, 0]} barSize={22} label={<TopNumLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 h-[140px]">
              <ResponsiveContainer>
                <AreaChart data={pipelineEffect} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="keepGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={low} stopOpacity={0.35} />
                      <stop offset="100%" stopColor={low} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="step" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis unit="%" domain={[0, 100]} tick={axisTick} axisLine={false} tickLine={false} width={32} />
                  <Tooltip content={<ChartTip />} />
                  <Area type="monotone" dataKey="keepRate" name="保留率" stroke={low} fill="url(#keepGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <CardTitle>有效性 · 一致性 · 时效性</CardTitle>
            <CardDesc>规则校验与随访可达性</CardDesc>
            <div className="mt-2 grid grid-cols-1 gap-3 md:grid-cols-3">
              {(
                [
                  { title: '有效性', data: dimensionBars.validity },
                  { title: '一致性', data: dimensionBars.consistency },
                  { title: '时效性', data: dimensionBars.timeliness },
                ] as const
              ).map((block) => (
                <div key={block.title}>
                  <div className="mb-1 text-[12px] font-medium">{block.title}</div>
                  <div className="h-[180px]">
                    <ResponsiveContainer>
                      <BarChart data={block.data} layout="vertical" margin={{ top: 0, right: 28, left: 0, bottom: 0 }}>
                        <XAxis type="number" domain={[0, 100]} hide />
                        <YAxis type="category" dataKey="name" width={88} tick={{ fill: '#8a8a8a', fontSize: 10 }} axisLine={false} tickLine={false} />
                        <Tooltip content={<ChartTip />} />
                        <Bar dataKey="value" name="%" fill={block.title === '时效性' ? 'url(#hatchHigh)' : low} radius={[0, 6, 6, 0]} barSize={10} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
          <Card>
            <CardTitle>代表性 / 标签质量</CardTitle>
            <CardDesc>队列坐实程度与标签可用性</CardDesc>
            <div className="mt-2 h-[230px]">
              <ResponsiveContainer>
                <BarChart
                  data={[...dimensionBars.representativeness, ...dimensionBars.label]}
                  layout="vertical"
                  margin={{ top: 4, right: 36, left: 4, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fill: '#8a8a8a', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="value" name="%" fill={low} radius={[0, 8, 8, 0]} barSize={12} label={<RightPctLabel />} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <CardTitle>可追溯性 · 列处置</CardTitle>
            <CardDesc>原始列如何分流到训练特征</CardDesc>
            <div className="mt-2 h-[230px]">
              <ResponsiveContainer>
                <BarChart data={columnDisposition} layout="vertical" margin={{ top: 4, right: 28, left: 4, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                  <XAxis type="number" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="step" width={96} tick={axisTick} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="n" name="列数" radius={[0, 8, 8, 0]} barSize={14} label={<TopNumLabel />}>
                    {columnDisposition.map((d, i) => (
                      <Cell key={d.step} fill={d.step === '进入训练' ? low : i === 0 ? low : 'url(#hatchHigh)'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <CardTitle>公平性补充 · 年龄覆盖</CardTitle>
            <CardDesc>按性别看 age 非空率差异</CardDesc>
            <div className="mt-2 h-[200px]">
              <ResponsiveContainer>
                <BarChart data={ageCoverageByGender} barCategoryGap="45%" margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="gender" tick={axisTick} axisLine={false} tickLine={false} />
                  <YAxis unit="%" domain={[0, 100]} tick={axisTick} axisLine={false} tickLine={false} width={32} />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="coverage" name="年龄非空率" radius={[8, 8, 0, 0]} barSize={28} label={<TopNumLabel />}>
                    {ageCoverageByGender.map((d) => (
                      <Cell key={d.gender} fill={d.gender === '男' ? low : high} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 h-[120px]">
              <ResponsiveContainer>
                <BarChart data={featureMissingBuckets} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
                  <XAxis dataKey="bucket" tick={{ fill: '#8a8a8a', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip content={<ChartTip />} />
                  <Bar dataKey="n" name="特征数" fill="url(#hatchHigh)" radius={[6, 6, 0, 0]} barSize={14} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-1 text-[11px] text-[var(--color-muted)]">下方小图：清洗后特征缺失率分箱。</p>
          </Card>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardTitle>关键字段缺失率：清洗前后</CardTitle>
            <CardDesc>after=0 且原缺失高者，多为剔除字段的占位对比</CardDesc>
            <div className="mt-2 h-[280px]">
              <ResponsiveContainer>
                <BarChart
                  data={keyFieldMissing.map((d) => ({
                    field: d.field,
                    before: d.before,
                    after: d.after ?? 0,
                  }))}
                  barGap={3}
                  barCategoryGap="28%"
                  margin={{ top: 22, right: 8, left: 0, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                  <XAxis dataKey="field" tick={{ fill: '#8a8a8a', fontSize: 10 }} axisLine={false} tickLine={false} interval={0} angle={-20} textAnchor="end" height={50} />
                  <YAxis unit="%" tick={axisTick} axisLine={false} tickLine={false} width={36} domain={[0, 100]} />
                  <Tooltip content={<ChartTip />} />
                  <Legend />
                  <Bar dataKey="before" name="处理前缺失%" fill="url(#hatchHigh)" radius={[6, 6, 0, 0]} barSize={12} />
                  <Bar dataKey="after" name="处理后缺失%" fill={low} radius={[6, 6, 0, 0]} barSize={12} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <CardTitle>字段角色构成 + 可追溯性得分</CardTitle>
            <CardDesc>原始列类型拆解，支撑可追溯性评估</CardDesc>
            <div className="mt-2 grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="h-[260px]">
                <ResponsiveContainer>
                  <BarChart data={columnRoles} layout="vertical" margin={{ top: 4, right: 28, left: 4, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                    <XAxis type="number" tick={axisTick} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="role" width={56} tick={axisTick} axisLine={false} tickLine={false} />
                    <Tooltip content={<ChartTip />} />
                    <Bar dataKey="n" name="列数" fill={low} radius={[0, 8, 8, 0]} barSize={12} label={<TopNumLabel />} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="h-[260px]">
                <ResponsiveContainer>
                  <BarChart data={dimensionBars.traceability} layout="vertical" margin={{ top: 4, right: 36, left: 4, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
                    <XAxis type="number" domain={[0, 100]} tick={axisTick} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="name" width={100} tick={{ fill: '#8a8a8a', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<ChartTip />} />
                    <Bar dataKey="value" name="得分" fill={low} radius={[0, 8, 8, 0]} barSize={14} label={<RightPctLabel />} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </Card>
        </div>
      </main>
    </div>
  )
}
