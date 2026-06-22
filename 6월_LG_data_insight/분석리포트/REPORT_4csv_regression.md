# 올리브영 브랜드 랭킹 회귀분석 — 4개 CSV 전용

종속변수 = brand_rank (낮을수록 상위). 전체 브랜드 universe n=665 (YT 노출보유 338, IG 노출보유 655).

수치변수는 count/views/subs에 log(x+1), 표준화 β는 z표준화 후. 부호 +는 'rank 숫자↑=하위로 밀림'.

### A. 유튜브 노출만  (n=337)

단변량 설명력 (R²=상관², r):
| 변수 | 단변량 R² | r |
|---|---|---|
| yt_n_videos | 0.2765 | -0.526 |
| yt_log_views | 0.2674 | -0.517 |
| yt_max_subs | 0.1214 | -0.348 |
| yt_max_viral | 0.0512 | -0.226 |
| yt_share_ppl | 0.0139 | +0.118 |
| yt_share_ads | 0.0086 | +0.093 |
| yt_median_views | 0.0017 | -0.041 |
| yt_median_subs | 0.0012 | -0.034 |
| yt_share_short | 0.0007 | +0.026 |
| yt_like_rate | 0.0000 | +0.002 |

전체 OLS (R²=0.3738, adj_R²=0.3546, n=337)
| 변수 | 표준화 β | p | 유의 |
|---|---|---|---|
| yt_log_views | -3.706 | 0.0000 | *** |
| yt_n_videos | -2.066 | 0.0000 | *** |
| yt_max_subs | +1.143 | 0.0589 |  |
| yt_median_views | +1.007 | 0.0364 | * |
| yt_share_short | -0.481 | 0.2072 |  |
| yt_median_subs | -0.479 | 0.3418 |  |
| yt_share_ads | +0.290 | 0.4664 |  |
| yt_max_viral | -0.239 | 0.4736 |  |
| yt_like_rate | -0.107 | 0.7716 |  |
| yt_share_ppl | -0.106 | 0.7909 |  |

### B. 인스타 노출만  (n=650)

단변량 설명력 (R²=상관², r):
| 변수 | 단변량 R² | r |
|---|---|---|
| ig_n_posts | 0.4236 | -0.651 |
| ig_log_likes | 0.2894 | -0.538 |
| ig_share_ppl | 0.0081 | -0.090 |
| ig_median_likes | 0.0016 | -0.040 |
| ig_share_reel | 0.0014 | -0.037 |
| ig_median_comments | 0.0000 | -0.007 |

전체 OLS (R²=0.4629, adj_R²=0.4579, n=650)
| 변수 | 표준화 β | p | 유의 |
|---|---|---|---|
| ig_n_posts | -2.895 | 0.0000 | *** |
| ig_log_likes | -1.408 | 0.0000 | *** |
| ig_median_comments | +0.225 | 0.2438 |  |
| ig_median_likes | -0.084 | 0.6875 |  |
| ig_share_ppl | +0.058 | 0.7454 |  |
| ig_share_reel | +0.003 | 0.9881 |  |

### C. 유튜브+인스타 결합  (n=326)

단변량 설명력 (R²=상관², r):
| 변수 | 단변량 R² | r |
|---|---|---|
| ig_n_posts | 0.3852 | -0.621 |
| ig_log_likes | 0.3178 | -0.564 |
| yt_n_videos | 0.2724 | -0.522 |
| yt_log_views | 0.2708 | -0.520 |
| yt_max_subs | 0.1228 | -0.350 |
| yt_max_viral | 0.0627 | -0.250 |
| yt_share_ppl | 0.0167 | +0.129 |
| ig_share_ppl | 0.0150 | -0.122 |
| yt_share_ads | 0.0114 | +0.107 |
| ig_share_reel | 0.0069 | -0.083 |
| yt_share_short | 0.0018 | +0.042 |
| yt_median_views | 0.0012 | -0.035 |
| ig_median_comments | 0.0006 | +0.025 |
| ig_median_likes | 0.0005 | +0.023 |
| yt_median_subs | 0.0005 | -0.023 |
| yt_like_rate | 0.0001 | -0.009 |

전체 OLS (R²=0.5118, adj_R²=0.4865, n=326)
| 변수 | 표준화 β | p | 유의 |
|---|---|---|---|
| ig_n_posts | -2.554 | 0.0000 | *** |
| yt_log_views | -2.228 | 0.0005 | *** |
| yt_max_subs | +1.184 | 0.0266 | * |
| ig_log_likes | -1.061 | 0.0215 | * |
| yt_median_subs | -0.972 | 0.0331 | * |
| yt_n_videos | -0.867 | 0.0312 | * |
| yt_median_views | +0.845 | 0.0551 |  |
| ig_median_comments | +0.555 | 0.1126 |  |
| ig_share_ppl | -0.525 | 0.1171 |  |
| yt_share_ppl | +0.355 | 0.3406 |  |
| yt_max_viral | -0.343 | 0.2642 |  |
| ig_share_reel | -0.268 | 0.3788 |  |
| ig_median_likes | -0.251 | 0.5304 |  |
| yt_share_short | +0.246 | 0.4974 |  |
| yt_share_ads | +0.236 | 0.5227 |  |
| yt_like_rate | -0.059 | 0.8634 |  |

### D. 노출 '질'만 (양 변수 제외 → 내생성 통제)  (n=326)

단변량 설명력 (R²=상관², r):
| 변수 | 단변량 R² | r |
|---|---|---|
| yt_max_subs | 0.1228 | -0.350 |
| yt_max_viral | 0.0627 | -0.250 |
| yt_share_ppl | 0.0167 | +0.129 |
| ig_share_ppl | 0.0150 | -0.122 |
| yt_share_ads | 0.0114 | +0.107 |
| ig_share_reel | 0.0069 | -0.083 |
| yt_share_short | 0.0018 | +0.042 |
| yt_median_views | 0.0012 | -0.035 |
| ig_median_comments | 0.0006 | +0.025 |
| ig_median_likes | 0.0005 | +0.023 |
| yt_median_subs | 0.0005 | -0.023 |
| yt_like_rate | 0.0001 | -0.009 |

전체 OLS (R²=0.1862, adj_R²=0.1550, n=326)
| 변수 | 표준화 β | p | 유의 |
|---|---|---|---|
| yt_max_subs | -2.250 | 0.0000 | *** |
| yt_max_viral | -1.138 | 0.0033 | ** |
| ig_share_ppl | -1.037 | 0.0112 | * |
| ig_share_reel | -0.461 | 0.2343 |  |
| yt_median_subs | +0.393 | 0.4822 |  |
| yt_share_ppl | +0.392 | 0.4108 |  |
| yt_share_ads | +0.332 | 0.4816 |  |
| yt_like_rate | -0.318 | 0.4617 |  |
| ig_median_comments | +0.305 | 0.4933 |  |
| yt_share_short | -0.109 | 0.8094 |  |
| yt_median_views | -0.102 | 0.8378 |  |
| ig_median_likes | -0.095 | 0.8439 |  |

### RandomForest 변수 중요도 (결합, n=326, in-sample R²=0.933 과적합주의)
| 변수 | 중요도 |
|---|---|
| ig_n_posts | 0.231 |
| yt_log_views | 0.189 |
| yt_n_videos | 0.183 |
| ig_log_likes | 0.083 |
| yt_share_ads | 0.046 |
| yt_share_ppl | 0.033 |
| yt_max_subs | 0.032 |
| yt_median_subs | 0.028 |
| yt_share_short | 0.027 |
| ig_median_likes | 0.025 |
| ig_share_reel | 0.023 |
| yt_max_viral | 0.023 |
| yt_median_views | 0.021 |
| ig_share_ppl | 0.021 |
| yt_like_rate | 0.020 |
| ig_median_comments | 0.016 |

### 보조: TOP10 브랜드 진입(brand_rank<=10) 단변량 로지스틱 pseudo-R²
| 변수 | pseudo-R² |
|---|---|
| ig_log_likes | 0.2723 |
| yt_log_views | 0.2629 |
| ig_n_posts | 0.2526 |
| yt_n_videos | 0.1008 |
| yt_max_subs | 0.0675 |
| yt_max_viral | 0.0457 |
| yt_share_ppl | 0.0172 |
| yt_share_ads | 0.0086 |
| ig_median_comments | 0.0051 |
| ig_share_ppl | 0.0044 |
| ig_median_likes | 0.0018 |
| ig_share_reel | 0.0014 |
| yt_median_views | 0.0012 |
| yt_like_rate | 0.0008 |
| yt_share_short | 0.0001 |
| yt_median_subs | 0.0000 |