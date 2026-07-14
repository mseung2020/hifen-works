import type { ChartConfig, DataTable } from './types'
import { isNumericColumn } from './dataParser'
import { seriesColor, DEFAULT_FONT, INK } from './palette'

/** 업로드된 데이터로부터 합리적인 기본 차트 설정을 자동 구성 */
export function makeDefaultConfig(table: DataTable): ChartConfig {
  const numericCols: number[] = []
  let categoryIndex = 0
  let categoryFound = false

  table.columns.forEach((_, i) => {
    if (isNumericColumn(table, i)) {
      numericCols.push(i)
    } else if (!categoryFound) {
      categoryIndex = i
      categoryFound = true
    }
  })

  // 숫자열이 x축 후보로 잡히지 않도록: 카테고리 못 찾으면 첫 열 사용
  const valueCols = numericCols.filter((i) => i !== categoryIndex)
  const usedCols = valueCols.length > 0 ? valueCols : numericCols

  return {
    categoryIndex,
    series: usedCols.map((colIndex, i) => ({
      columnIndex: colIndex,
      name: table.columns[colIndex],
      type: 'bar',
      color: seriesColor(i),
      barRadius: 4,
      smooth: false,
      area: false,
      showLabel: false,
    })),
    title: '',
    showTitle: false,
    showLegend: usedCols.length >= 2,
    showXAxis: true,
    showYAxis: true,
    showGrid: true,
    fontFamily: DEFAULT_FONT,
    fontColor: INK.primary,
    fontSize: 12,
    width: 800,
    height: 500,
    transparent: true,
    backgroundColor: '#ffffff',
  }
}
