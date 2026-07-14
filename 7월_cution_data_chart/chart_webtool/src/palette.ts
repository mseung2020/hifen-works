// dataviz 스킬의 검증된 기본 팔레트 (light 모드, CVD-safe 순서)
export const CATEGORICAL: string[] = [
  '#2a78d6', // blue
  '#1baf7a', // aqua
  '#eda100', // yellow
  '#008300', // green
  '#4a3aa7', // violet
  '#e34948', // red
  '#e87ba4', // magenta
  '#eb6834', // orange
]

export const INK = {
  primary: '#0b0b0b',
  secondary: '#52514e',
  muted: '#898781',
  grid: '#e1e0d9',
  baseline: '#c3c2b7',
}

export const DEFAULT_FONT =
  'system-ui, -apple-system, "Segoe UI", "Apple SD Gothic Neo", sans-serif'

/** index로 계열 색을 가져오되, 8개를 넘으면 순환 */
export function seriesColor(i: number): string {
  return CATEGORICAL[i % CATEGORICAL.length]
}
