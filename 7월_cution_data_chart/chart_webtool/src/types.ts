// 앱 전역에서 쓰는 데이터/설정 타입 정의

export type CellValue = string | number | null

/** 업로드/편집된 원본 데이터 (엑셀처럼 열 이름 + 행들) */
export interface DataTable {
  columns: string[]
  rows: CellValue[][]
}

export type SeriesType = 'bar' | 'line'

/** 하나의 데이터 계열(막대/선 하나) 설정 */
export interface SeriesConfig {
  /** 이 계열이 어떤 열에서 값을 가져오는지 (columns 배열의 index) */
  columnIndex: number
  name: string
  type: SeriesType
  color: string
  /** 막대: 둥근 정도 / 선: 사용 안 함 */
  barRadius: number
  /** 선: 부드러운 곡선 여부 */
  smooth: boolean
  /** 선: 영역 채우기 여부 */
  area: boolean
  /** 각 값 위에 숫자 라벨 표시 */
  showLabel: boolean
}

/** 차트 전체 설정 */
export interface ChartConfig {
  /** x축(카테고리)으로 쓸 열 index */
  categoryIndex: number
  series: SeriesConfig[]

  title: string
  showTitle: boolean
  showLegend: boolean
  showXAxis: boolean
  showYAxis: boolean
  showGrid: boolean

  fontFamily: string
  fontColor: string
  fontSize: number

  /** 내보낼 캔버스 크기 */
  width: number
  height: number
  /** PNG 배경: 투명 or 지정 색 */
  transparent: boolean
  backgroundColor: string
}
