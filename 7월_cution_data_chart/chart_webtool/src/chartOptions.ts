import type { EChartsOption } from 'echarts'
import type { ChartConfig, DataTable } from './types'
import { INK } from './palette'

/** ChartConfig + DataTable → ECharts 옵션 객체 */
export function buildOption(table: DataTable, config: ChartConfig): EChartsOption {
  const categories = table.rows.map((r) => {
    const v = r[config.categoryIndex]
    return v === null ? '' : String(v)
  })

  const textStyle = {
    fontFamily: config.fontFamily,
    color: config.fontColor,
    fontSize: config.fontSize,
  }

  const series = config.series.map((s) => {
    const data = table.rows.map((r) => {
      const v = r[s.columnIndex]
      return typeof v === 'number' ? v : null
    })

    const common = {
      name: s.name,
      type: s.type,
      data,
      itemStyle: { color: s.color },
      label: {
        show: s.showLabel,
        position: s.type === 'bar' ? ('top' as const) : ('top' as const),
        color: config.fontColor,
        fontFamily: config.fontFamily,
        fontSize: config.fontSize - 1,
      },
    }

    if (s.type === 'bar') {
      return {
        ...common,
        barMaxWidth: 48,
        itemStyle: {
          color: s.color,
          borderRadius: [s.barRadius, s.barRadius, 0, 0] as [number, number, number, number],
        },
      }
    }
    // line
    return {
      ...common,
      smooth: s.smooth,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { width: 2, color: s.color },
      areaStyle: s.area ? { opacity: 0.15 } : undefined,
    }
  })

  return {
    // 화면 프리뷰용 배경 (내보내기 시엔 별도 처리)
    backgroundColor: 'transparent',
    textStyle,
    title: config.showTitle
      ? {
          text: config.title,
          left: 'center',
          textStyle: { ...textStyle, fontSize: config.fontSize + 6, fontWeight: 'bold' },
        }
      : undefined,
    legend:
      config.showLegend && config.series.length >= 1
        ? { bottom: 0, textStyle }
        : undefined,
    grid: {
      left: 48,
      right: 24,
      top: config.showTitle ? 56 : 24,
      bottom: config.showLegend ? 48 : 32,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: categories,
      show: config.showXAxis,
      axisLine: { lineStyle: { color: INK.baseline } },
      axisTick: { show: false },
      axisLabel: { color: config.fontColor, fontFamily: config.fontFamily, fontSize: config.fontSize },
    },
    yAxis: {
      type: 'value',
      show: config.showYAxis,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: config.showGrid, lineStyle: { color: INK.grid } },
      axisLabel: { color: config.fontColor, fontFamily: config.fontFamily, fontSize: config.fontSize },
    },
    series,
  }
}
