import { useRef, useState } from 'react'
import type { DataTable } from '../types'
import { parseFile } from '../dataParser'

interface Props {
  table: DataTable | null
  onData: (table: DataTable) => void
}

export default function DataPanel({ table, onData }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleFile(file: File) {
    setError(null)
    try {
      const parsed = await parseFile(file)
      if (parsed.columns.length === 0) {
        setError('데이터를 읽지 못했어요. 파일 내용을 확인해주세요.')
        return
      }
      onData(parsed)
    } catch (e) {
      setError('파일을 여는 중 오류가 났어요: ' + (e as Error).message)
    }
  }

  return (
    <div className="panel left">
      <div className="section">
        <h2>데이터</h2>
        <div
          className={'dropzone' + (dragging ? ' drag' : '')}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragging(false)
            const f = e.dataTransfer.files[0]
            if (f) handleFile(f)
          }}
        >
          CSV · 엑셀(xlsx) 파일을
          <br />
          여기에 끌어놓거나 클릭해서 선택
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.txt,.xlsx,.xls"
          style={{ display: 'none' }}
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) handleFile(f)
            e.target.value = ''
          }}
        />
        {error && <p style={{ color: '#d03b3b', fontSize: 12 }}>{error}</p>}
      </div>

      {table && (
        <div className="section">
          <h2>미리보기 ({table.rows.length}행)</h2>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  {table.columns.map((c, i) => (
                    <th key={i}>{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.slice(0, 8).map((row, ri) => (
                  <tr key={ri}>
                    {row.map((cell, ci) => (
                      <td key={ci}>{cell === null ? '' : String(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {table.rows.length > 8 && (
            <p className="hint">…외 {table.rows.length - 8}행</p>
          )}
        </div>
      )}
    </div>
  )
}
