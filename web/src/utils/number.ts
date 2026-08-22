/**
 * 格式化数字展示：整数显示为 int，非整数显示为 float
 * 例如：332.00 → "332"，5.93 → "5.93"
 */
export function formatNumber(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '-'
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '-'
  return Number.isInteger(num) ? num.toString() : num.toString()
}
