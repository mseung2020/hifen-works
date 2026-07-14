import { useRef, useState } from 'react'
import type { ChartConfig, DataTable } from './types'
import { makeDefaultConfig } from './defaultConfig'
import DataPanel from './components/DataPanel'
import StylePanel from './components/StylePanel'
import ChartCanvas, { type ChartCanvasHandle } from './components/ChartCanvas'

export default function App() {
  const [table, setTable] = useState<DataTable | null>(null)
  const [config, setConfig] = useState<ChartConfig | null>(null)
  const chartRef = useRef<ChartCanvasHandle>(null)

  function handleData(t: DataTable) {
    setTable(t)
    setConfig(makeDefaultConfig(t))
  }

  function handleExport() {
    const url = chartRef.current?.exportPng()
    if (!url) return
    const a = document.createElement('a')
    a.href = url
    a.download = 'chart.png'
    a.click()
  }

  return (
    <div className="app">
      <div className="topbar">
        <h1>Cution 데이터 차트</h1>
        <button className="primary" onClick={handleExport} disabled={!table}>
          투명 PNG 내보내기
        </button>
      </div>

      <div className="main">
        <DataPanel table={table} onData={handleData} />

        <div className="stage">
          {table && config ? (
            <div className="chart-frame">
              <ChartCanvas ref={chartRef} table={table} config={config} />
            </div>
          ) : (
            <div className="empty">
              왼쪽에서 CSV·엑셀 파일을 올리면
              <br />
              여기에 차트가 나타납니다.
            </div>
          )}
        </div>

        {table && config ? (
          <StylePanel table={table} config={config} onChange={setConfig} />
        ) : (
          <div className="panel right">
            <p className="hint">데이터를 올리면 여기에서 색·모양·축을 세밀하게 조절할 수 있어요.</p>
          </div>
        )}
      </div>
    </div>
  )
}
