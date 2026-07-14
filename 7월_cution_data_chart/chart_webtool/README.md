# Cution 데이터 차트

CSV·엑셀 데이터를 올려서 막대·선 그래프를 만들고, **투명 배경 PNG**로 내보내는 웹 툴.

## 실행

```bash
npm install      # 최초 1회
npm run dev      # http://localhost:5173
```

## 사용 흐름

1. 왼쪽 패널에 CSV/엑셀(xlsx) 파일을 끌어놓거나 클릭해서 선택
2. 가운데에 차트가 자동으로 그려짐 (체커보드 배경 = 투명 영역)
3. 오른쪽 패널에서 세밀하게 커스텀
   - **축·데이터**: X축(카테고리) 열 선택
   - **계열**: 막대/선 종류, 색, 막대 둥글기, 곡선/영역, 값 라벨, 계열 추가·삭제
   - **제목·요소**: 제목, 범례, X/Y축, 격자선 토글
   - **글꼴**: 크기·색
   - **내보내기**: 캔버스 크기, 투명 배경 on/off, 배경 색
4. 우상단 **투명 PNG 내보내기** → `chart.png` 다운로드 (3배 고해상도)

## 기술 스택

- React + Vite + TypeScript
- ECharts (차트 + 투명 PNG 내보내기)
- PapaParse (CSV) · SheetJS (엑셀)

## 구조

```
src/
  types.ts          데이터·설정 타입
  palette.ts        기본 색상 팔레트 (CVD-safe)
  dataParser.ts     CSV/엑셀 파싱
  defaultConfig.ts  업로드 데이터 → 기본 차트 설정 자동 생성
  chartOptions.ts   설정 → ECharts 옵션 변환
  components/
    DataPanel.tsx   업로드 + 데이터 미리보기 (왼쪽)
    ChartCanvas.tsx 차트 렌더 + PNG 내보내기 (가운데)
    StylePanel.tsx  커스텀 컨트롤 (오른쪽)
  App.tsx           전체 레이아웃·상태
```
