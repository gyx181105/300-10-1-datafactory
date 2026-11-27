export function TopNumLabel(props: {
  x?: number
  y?: number
  width?: number
  value?: number | string
}) {
  const { x = 0, y = 0, width = 0, value } = props
  if (value == null || Number.isNaN(Number(value))) return null
  return (
    <text x={x + width / 2} y={y - 6} textAnchor="middle" fill="#6b7280" fontSize={11}>
      {Number(value).toLocaleString()}
    </text>
  )
}

export function RightPctLabel(props: {
  x?: number
  y?: number
  width?: number
  height?: number
  value?: number | string
}) {
  const { x = 0, y = 0, width = 0, height = 0, value } = props
  if (value == null || Number.isNaN(Number(value))) return null
  return (
    <text
      x={x + width + 6}
      y={y + height / 2}
      textAnchor="start"
      dominantBaseline="middle"
      fill="#6b7280"
      fontSize={11}
    >
      {`${value}%`}
    </text>
  )
}

export function RightNumLabel(props: {
  x?: number
  y?: number
  width?: number
  height?: number
  value?: number | string
}) {
  const { x = 0, y = 0, width = 0, height = 0, value } = props
  if (value == null || Number.isNaN(Number(value))) return null
  return (
    <text
      x={x + width + 6}
      y={y + height / 2}
      textAnchor="start"
      dominantBaseline="middle"
      fill="#6b7280"
      fontSize={11}
    >
      {Number(value).toLocaleString()}
    </text>
  )
}

export function PieOuterLabel(props: {
  cx?: number
  cy?: number
  midAngle?: number
  outerRadius?: number
  value?: number
  percent?: number
}) {
  const { cx = 0, cy = 0, midAngle = 0, outerRadius = 0, value, percent = 0 } = props
  if (value == null) return null
  const RADIAN = Math.PI / 180
  const sin = Math.sin(-midAngle * RADIAN)
  const cos = Math.cos(-midAngle * RADIAN)
  const sx = cx + (outerRadius + 4) * cos
  const sy = cy + (outerRadius + 4) * sin
  const mx = cx + (outerRadius + 16) * cos
  const my = cy + (outerRadius + 16) * sin
  const ex = mx + (cos >= 0 ? 1 : -1) * 12
  const ey = my
  return (
    <g>
      <path d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`} stroke="#9ca3af" fill="none" strokeWidth={1} />
      <circle cx={ex} cy={ey} r={2} fill="#9ca3af" />
      <text
        x={ex + (cos >= 0 ? 6 : -6)}
        y={ey}
        textAnchor={cos >= 0 ? 'start' : 'end'}
        dominantBaseline="central"
        fill="#6b7280"
        fontSize={11}
      >
        {`${Number(value).toLocaleString()}（${(percent * 100).toFixed(1)}%）`}
      </text>
    </g>
  )
}
