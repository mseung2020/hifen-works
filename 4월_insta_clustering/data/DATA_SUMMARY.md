# 데이터 요약

이 앱이 **실제로 사용하는 데이터(`real data_all2.csv`, 948K, 2,410행)는 레포에 포함**되어 있어 그대로 실행됩니다. 아래는 그 원천이 된 대용량 raw 데이터의 요약입니다.

## 제외된 원본: `real data_all.csv` (959MB)
- **규모:** 2,225,026행 (포스트 단위 raw 데이터)
- GitHub 100MB 제한 초과로 제외. 앞 49행 샘플은 `real_data_all.sample.csv` 참조
- **컬럼:** `id, analysis_date, cluster_id, cluster_name, sub_keyword, created_at, updated_at, topic_total_post_count, topic_total_dm_count, topic, cluster_post_share, cluster_dm_share, dm_per_views, dm_per_likes, cluster_post_count, cluster_dm_send_count, cluster_views, cluster_likes, cluster_name_reason, top1~3_post_id` 등

## 포함된 앱 데이터: `real data_all2.csv` (앱 입력, 2,410행)
포스트 단위 raw를 **클러스터 단위로 집계**한 결과. 컬럼:
`cluster_id, sub_keyword, analysis_date, topic_total_post_count, topic_total_dm_count, cluster_name, topic, cluster_post_share, cluster_dm_share, dm_per_views, dm_per_likes, cluster_post_count, cluster_dm_send_count, cluster_views, cluster_likes, cluster_name_reason, top1~3_post_id, created_at, updated_at`

> 4분면 버블차트는 이 클러스터 집계 데이터(클러스터별 포스트/DM 점유율, dm/조회수 효율 등)를 좌표·버블 크기로 시각화합니다.
