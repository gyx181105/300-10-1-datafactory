/** margin 风格斜线填充，随当前 palette 变化 */
export function ChartPatterns({ high, low }: { high: string; low: string }) {
  return (
    <svg width={0} height={0} className="absolute">
      <defs>
        <pattern id="hatchLow" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
          <rect width="6" height="6" fill={low} fillOpacity={0.18} />
          <line x1="0" y1="0" x2="0" y2="6" stroke={low} strokeWidth="2.2" />
        </pattern>
        <pattern id="hatchHigh" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
          <rect width="6" height="6" fill={high} fillOpacity={0.18} />
          <line x1="0" y1="0" x2="0" y2="6" stroke={high} strokeWidth="2.2" />
        </pattern>
      </defs>
    </svg>
  )
}
