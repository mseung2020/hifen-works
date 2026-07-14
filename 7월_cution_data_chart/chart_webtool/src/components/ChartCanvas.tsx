import { forwardRef, useImperativeHandle, useRef } from 'react'
import ReactECharts from 'echarts-for-react'
import type { ChartConfig, DataTable } from '../types'
import { buildOption } from '../chartOptions'

export interface ChartCanvasHandle {
  /** 현재 차트를 PNG dataURL로 반환 (투명/배경 옵션 반영) */
  exportPng: () => string | null
}

interface Props {
  table: DataTable
  config: ChartConfig
}

const ChartCanvas = forwardRef<ChartCanvasHandle, Props>(({ table, config }, ref) => {
  const chartRef = useRef<ReactECharts>(null)

  useImperativeHandle(ref, () => ({
    exportPng: () => {
      const inst = chartRef.current?.getEchartsInstance()
      if (!inst) return null
      return inst.getDataURL({
        type: 'png',
        pixelRatio: 3, // 고해상도 내보내기
        backgroundColor: config.transparent ? 'transparent' : config.backgroundColor,
      })
    },
  }))

  const option = buildOption(table, config)

  return (
    <ReactECharts
      ref={chartRef}
      option={option}
      notMerge
      style={{ width: config.width, height: config.height }}
      opts={{ renderer: 'canvas' }}
    />
  )
})

ChartCanvas.displayName = 'ChartCanvas'
export default ChartCanvas
