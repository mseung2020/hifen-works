import type { ChartConfig, DataTable, SeriesConfig } from '../types'
import { seriesColor } from '../palette'

interface Props {
  table: DataTable
  config: ChartConfig
  onChange: (config: ChartConfig) => void
}

export default function StylePanel({ table, config, onChange }: Props) {
  function patch(p: Partial<ChartConfig>) {
    onChange({ ...config, ...p })
  }

  function patchSeries(idx: number, p: Partial<SeriesConfig>) {
    const series = config.series.map((s, i) => (i === idx ? { ...s, ...p } : s))
    onChange({ ...config, series })
  }

  function addSeries() {
    // 아직 안 쓰인 열 중 하나를 추가
    const used = new Set(config.series.map((s) => s.columnIndex))
    let colIndex = table.columns.findIndex((_, i) => i !== config.categoryIndex && !used.has(i))
    if (colIndex === -1) colIndex = 0
    const next: SeriesConfig = {
      columnIndex: colIndex,
      name: table.columns[colIndex] ?? `계열 ${config.series.length + 1}`,
      type: 'bar',
      color: seriesColor(config.series.length),
      barRadius: 4,
      smooth: false,
      area: false,
      showLabel: false,
    }
    onChange({ ...config, series: [...config.series, next] })
  }

  function removeSeries(idx: number) {
    onChange({ ...config, series: config.series.filter((_, i) => i !== idx) })
  }

  return (
    <div className="panel right">
      {/* ===== 데이터 매핑 ===== */}
      <div className="section">
        <h2>축 · 데이터</h2>
        <div className="field">
          <label>X축 (카테고리)</label>
          <select
            value={config.categoryIndex}
            onChange={(e) => patch({ categoryIndex: Number(e.target.value) })}
          >
            {table.columns.map((c, i) => (
              <option key={i} value={i}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* ===== 계열 ===== */}
      <div className="section">
        <h2>계열 (막대 · 선)</h2>
        {config.series.map((s, idx) => (
          <div className="series-card" key={idx}>
            <div className="head">
              <strong>계열 {idx + 1}</strong>
              <button className="btn-x" title="삭제" onClick={() => removeSeries(idx)}>
                ×
              </button>
            </div>

            <div className="field">
              <label>데이터 열</label>
              <select
                value={s.columnIndex}
                onChange={(e) => {
                  const ci = Number(e.target.value)
                  patchSeries(idx, { columnIndex: ci, name: table.columns[ci] })
                }}
              >
                {table.columns.map((c, i) => (
                  <option key={i} value={i}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label>이름</label>
              <input
                type="text"
                value={s.name}
                onChange={(e) => patchSeries(idx, { name: e.target.value })}
              />
            </div>

            <div className="row">
              <div className="field" style={{ flex: 1 }}>
                <label>종류</label>
                <select
                  value={s.type}
                  onChange={(e) => patchSeries(idx, { type: e.target.value as SeriesConfig['type'] })}
                >
                  <option value="bar">막대</option>
                  <option value="line">선</option>
                </select>
              </div>
              <div className="field">
                <label>색</label>
                <input
                  type="color"
                  value={s.color}
                  onChange={(e) => patchSeries(idx, { color: e.target.value })}
                />
              </div>
            </div>

            {s.type === 'bar' && (
              <div className="field">
                <label>막대 둥글기 ({s.barRadius}px)</label>
                <input
                  type="range"
                  min={0}
                  max={24}
                  value={s.barRadius}
                  style={{ width: '100%' }}
                  onChange={(e) => patchSeries(idx, { barRadius: Number(e.target.value) })}
                />
              </div>
            )}

            {s.type === 'line' && (
              <>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={s.smooth}
                    onChange={(e) => patchSeries(idx, { smooth: e.target.checked })}
                  />
                  부드러운 곡선
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={s.area}
                    onChange={(e) => patchSeries(idx, { area: e.target.checked })}
                  />
                  영역 채우기
                </label>
              </>
            )}

            <label className="check">
              <input
                type="checkbox"
                checked={s.showLabel}
                onChange={(e) => patchSeries(idx, { showLabel: e.target.checked })}
              />
              값 라벨 표시
            </label>
          </div>
        ))}
        <button onClick={addSeries}>+ 계열 추가</button>
      </div>

      {/* ===== 제목 · 요소 ===== */}
      <div className="section">
        <h2>제목 · 요소</h2>
        <label className="check">
          <input
            type="checkbox"
            checked={config.showTitle}
            onChange={(e) => patch({ showTitle: e.target.checked })}
          />
          제목 표시
        </label>
        {config.showTitle && (
          <div className="field">
            <input
              type="text"
              placeholder="차트 제목"
              value={config.title}
              onChange={(e) => patch({ title: e.target.value })}
            />
          </div>
        )}
        <label className="check">
          <input
            type="checkbox"
            checked={config.showLegend}
            onChange={(e) => patch({ showLegend: e.target.checked })}
          />
          범례 표시
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={config.showXAxis}
            onChange={(e) => patch({ showXAxis: e.target.checked })}
          />
          X축 표시
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={config.showYAxis}
            onChange={(e) => patch({ showYAxis: e.target.checked })}
          />
          Y축 표시
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={config.showGrid}
            onChange={(e) => patch({ showGrid: e.target.checked })}
          />
          가로 격자선
        </label>
      </div>

      {/* ===== 글꼴 ===== */}
      <div className="section">
        <h2>글꼴</h2>
        <div className="row">
          <div className="field" style={{ flex: 1 }}>
            <label>글자 크기 ({config.fontSize}px)</label>
            <input
              type="range"
              min={8}
              max={28}
              value={config.fontSize}
              style={{ width: '100%' }}
              onChange={(e) => patch({ fontSize: Number(e.target.value) })}
            />
          </div>
          <div className="field">
            <label>색</label>
            <input
              type="color"
              value={config.fontColor}
              onChange={(e) => patch({ fontColor: e.target.value })}
            />
          </div>
        </div>
      </div>

      {/* ===== 내보내기 ===== */}
      <div className="section">
        <h2>내보내기 크기 · 배경</h2>
        <div className="row">
          <div className="field" style={{ flex: 1 }}>
            <label>가로(px)</label>
            <input
              type="number"
              value={config.width}
              onChange={(e) => patch({ width: Number(e.target.value) })}
            />
          </div>
          <div className="field" style={{ flex: 1 }}>
            <label>세로(px)</label>
            <input
              type="number"
              value={config.height}
              onChange={(e) => patch({ height: Number(e.target.value) })}
            />
          </div>
        </div>
        <label className="check">
          <input
            type="checkbox"
            checked={config.transparent}
            onChange={(e) => patch({ transparent: e.target.checked })}
          />
          투명 배경 (PNG)
        </label>
        {!config.transparent && (
          <div className="field">
            <label>배경 색</label>
            <input
              type="color"
              value={config.backgroundColor}
              onChange={(e) => patch({ backgroundColor: e.target.value })}
            />
          </div>
        )}
      </div>
    </div>
  )
}
