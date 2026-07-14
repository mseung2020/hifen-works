import Papa from 'papaparse'
import * as XLSX from 'xlsx'
import type { CellValue, DataTable } from './types'

/** 문자열이 숫자로 해석 가능하면 number, 아니면 원본 문자열로 변환 */
function coerce(value: unknown): CellValue {
  if (value === null || value === undefined || value === '') return null
  if (typeof value === 'number') return value
  const s = String(value).trim()
  // 쉼표가 들어간 숫자(예: "1,234")도 숫자로 인식
  const cleaned = s.replace(/,/g, '')
  if (cleaned !== '' && !isNaN(Number(cleaned))) return Number(cleaned)
  return s
}

/** 2차원 배열(첫 행 = 헤더)을 DataTable로 정규화 */
function fromMatrix(matrix: unknown[][]): DataTable {
  const nonEmpty = matrix.filter(
    (r) => Array.isArray(r) && r.some((c) => c !== null && c !== undefined && c !== ''),
  )
  if (nonEmpty.length === 0) return { columns: [], rows: [] }

  const header = nonEmpty[0].map((c, i) =>
    c === null || c === undefined || String(c).trim() === '' ? `열 ${i + 1}` : String(c).trim(),
  )
  const rows = nonEmpty.slice(1).map((r) => {
    const row: CellValue[] = []
    for (let i = 0; i < header.length; i++) row.push(coerce(r[i]))
    return row
  })
  return { columns: header, rows }
}

export async function parseFile(file: File): Promise<DataTable> {
  const name = file.name.toLowerCase()
  if (name.endsWith('.csv') || name.endsWith('.txt')) {
    return parseCsv(await file.text())
  }
  // 엑셀(xlsx/xls) 및 기타는 SheetJS로 처리
  const buf = await file.arrayBuffer()
  const wb = XLSX.read(buf, { type: 'array' })
  const first = wb.SheetNames[0]
  const sheet = wb.Sheets[first]
  const matrix = XLSX.utils.sheet_to_json<unknown[]>(sheet, { header: 1, defval: '' })
  return fromMatrix(matrix)
}

export function parseCsv(text: string): DataTable {
  const result = Papa.parse<string[]>(text, {
    skipEmptyLines: true,
  })
  return fromMatrix(result.data)
}

/** 특정 열이 숫자 데이터인지 판단 (값 계열 후보 찾기용) */
export function isNumericColumn(table: DataTable, colIndex: number): boolean {
  let numeric = 0
  let total = 0
  for (const row of table.rows) {
    const v = row[colIndex]
    if (v === null) continue
    total++
    if (typeof v === 'number') numeric++
  }
  return total > 0 && numeric / total >= 0.6
}
