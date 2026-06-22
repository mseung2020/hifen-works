# 랭킹 설명력 분석 — 순수 통계

해석·인사이트 없이 수치만 기록. 변수별 설명력을 단변량 R², 전체모형 표준화계수, RandomForest 중요도 3가지로 산출.

- **종속 A**: 실제 최고 올영 랭킹 `best_rank` (oy_trend, 연속·낮을수록 상위), n=585
- **종속 B**: `reached_top10` TOP10 도달 (CSV product universe, 이진), n=973 (양성 617)
- 수치변수는 count/views/subs/price에 `log(x+1)` 적용. 표준화계수는 z-표준화 후.

---

## 요약 — 단변량 설명력 순위 (랭킹을 가장 잘 설명하는 변수)

| 순위 | 종속 A (best_rank) 단변량 R² | 종속 B (TOP10) pseudo-R² |
|---|---|---|
| 1 | **category (범주) 0.0407** | **price 0.0873** |
| 2 | **price 0.0118** | median_views 0.0152 |
| 3 | share_ppl 0.0032 | total_views 0.0070 |
| 4 | max_viral_ratio 0.0016 | n_channels 0.0059 |
| 5 | n_channels 0.0015 | median_subs 0.0057 |

→ 두 종속변수 모두에서 **`price`가 (범주형 category 제외 시) 최상위 단변량 설명변수**. 유튜브 노출/규모 변수는 모두 하위.

---

## A. 종속변수 = 실제 최고 올영 랭킹 `best_rank` (n=585)

### A-1. 단변량 설명력 (R² = 상관²)
| 변수 | 단변량 R² | 상관 r |
|---|---|---|
| category (범주) | 0.0407 | — |
| price | 0.0118 | 0.109 |
| share_ppl | 0.0032 | 0.057 |
| max_viral_ratio | 0.0016 | 0.040 |
| n_channels | 0.0015 | −0.039 |
| n_videos | 0.0014 | −0.038 |
| share_ads | 0.0014 | 0.037 |
| median_subs | 0.0005 | −0.021 |
| share_short | 0.0004 | 0.020 |
| max_subs | 0.0001 | 0.008 |
| median_views | 0.0000 | 0.006 |
| avg_like_rate | 0.0000 | 0.003 |
| total_views | 0.0000 | 0.000 |

### A-2. 전체 OLS — 표준화계수·p값 (전체모형 R²=0.0268, adj_R²=0.0063)
| 변수 | 표준화 β | p | 유의 |
|---|---|---|---|
| n_channels | −0.257 | 0.350 | |
| total_views | 0.144 | 0.178 | |
| median_subs | −0.109 | 0.148 | |
| price | 0.108 | 0.011 | * |
| n_videos | 0.067 | 0.813 | |
| max_viral_ratio | 0.051 | 0.265 | |
| median_views | 0.045 | 0.541 | |
| share_ppl | 0.034 | 0.589 | |
| max_subs | 0.028 | 0.635 | |
| avg_like_rate | 0.028 | 0.557 | |
| share_ads | 0.015 | 0.818 | |
| share_short | 0.012 | 0.846 | |

### A-3. RandomForest 변수 중요도 (category 더미 합산=0.0739)
| 변수 | 중요도 |
|---|---|
| share_ads | 0.170 |
| price | 0.164 |
| share_ppl | 0.113 |
| avg_like_rate | 0.102 |
| max_subs | 0.075 |
| total_views | 0.066 |
| n_videos | 0.059 |
| share_short | 0.056 |
| max_viral_ratio | 0.052 |
| median_subs | 0.027 |
| median_views | 0.022 |
| n_channels | 0.020 |

> 주: RF in-sample R²=0.85는 과적합(표본내). 중요도 순위 참고용. 전체 OLS 설명력(R²=0.027)은 매우 낮음.

---

## B. 종속변수 = TOP10 도달 (이진, n=973, 양성 617)

### B-1. 단변량 설명력 (McFadden pseudo-R²)
| 변수 | pseudo-R² |
|---|---|
| price | 0.0873 |
| median_views | 0.0152 |
| total_views | 0.0070 |
| n_channels | 0.0059 |
| median_subs | 0.0057 |
| max_subs | 0.0042 |
| n_videos | 0.0041 |
| share_ppl | 0.0031 |
| share_short | 0.0029 |
| share_ads | 0.0005 |
| max_viral_ratio | 0.0000 |
| avg_like_rate | 0.0000 |

### B-2. 전체 Logit — 표준화계수·p값 (전체모형 pseudo-R²=0.1741)
| 변수 | 표준화 β | p | 유의 |
|---|---|---|---|
| n_channels | 2.012 | 0.0002 | *** |
| n_videos | −1.457 | 0.0063 | ** |
| price | −1.096 | 0.0000 | *** |
| median_views | 0.538 | 0.0001 | *** |
| share_short | 0.316 | 0.0021 | ** |
| share_ppl | −0.251 | 0.0174 | * |
| share_ads | 0.179 | 0.1053 | |
| max_viral_ratio | −0.074 | 0.347 | |
| total_views | 0.053 | 0.819 | |
| avg_like_rate | 0.052 | 0.530 | |
| median_subs | 0.025 | 0.842 | |
| max_subs | 0.020 | 0.877 | |

### B-3. RandomForest 변수 중요도
| 변수 | 중요도 |
|---|---|
| price | 0.185 |
| median_views | 0.099 |
| avg_like_rate | 0.083 |
| total_views | 0.081 |
| median_subs | 0.080 |
| max_subs | 0.077 |
| share_short | 0.077 |
| n_videos | 0.066 |
| max_viral_ratio | 0.066 |
| n_channels | 0.063 |
| share_ppl | 0.063 |
| share_ads | 0.060 |

---

## 방법·수치 주의 (해석 아님)
- `n_channels`와 `n_videos`는 상관 0.99 → B-2에서 표준화계수 부호가 반대로 큼(다중공선성/억제효과). 단변량(B-1)에선 각각 0.0059 / 0.0041.
- 전체모형 설명력: A R²=0.027(낮음), B pseudo-R²=0.174.
- `price`·`category`·`best_rank`는 oy_trend 출처. 그 외 변수는 올리브영 TOP 비디오 CSV 출처.
- 코드: `analysis/explanatory_power.py`
