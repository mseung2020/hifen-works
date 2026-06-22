-- ============================================================
-- LG생활건강 마케팅 대시보드용 데이터 추출 쿼리
-- MySQL Workbench에서 각 쿼리를 개별 실행 후 CSV로 저장하세요
-- 저장 위치: data/LG/
-- ============================================================
-- 대상 채널 수: 112개
-- 브랜드: 메디큐브, 라네즈, 이니스프리, 에스트라, 설화수, 케라스타즈, 정샘물, 덴티스테


-- ============================================================
-- [요청 1] LG생활건강 크리에이터들의 "모든 브랜드 협업 영상"
-- 목적: 경쟁사 자동 탐지
-- 저장: brand_all_videos.csv
-- ============================================================
SELECT
    b.channel_id,
    b.channel_title,
    b.brand1,
    b.brand2,
    b.brand3,
    b.video_id,
    b.views,
    b.likes,
    b.comments,
    b.channel_cost,
    b.publishDate,
    b.cpv,
    b.title
FROM brand b
WHERE b.channel_id IN ('UCwtLb11h7aai6EVcdwdlVJA', 'UCBoQ8_HIOVbOA_FuYtTapqA', 'UCRiIf6rt91BVfZVtURRXlOw', 'UCBlIcpkzSdcmp5G0XS7UsZA', 'UCff7sQ_kjCEPZvr8h8US8ww', 'UCun4wV8czkKcdMn_NDX8MIQ', 'UCfM7HC0wkS_cWVIcgpy2XPA', 'UCZ75Bt8hZt1AO2zRw36QJHw', 'UC26RKCp5GM9XxygDjikvtxw', 'UC4bNn3K-ivge2a_etU2jP9A', 'UCVRAHN1wuI9pUDyeSAc_I1A', 'UCM3LKBTSr8fUivTfrvOPZCg', 'UCvKl2U_gJeXRYGJKecvPcYA', 'UCA5CvI96Q7XtiRIxmajRzWw', 'UCPur_FJRVR-vKvAz1xvwq6w', 'UCx0ZL5ldCGMqkOGqyO1qOkw', 'UCkh6TlSape86-iHiehXvsmA', 'UCZCvbWrBFGQeZwf5qczqLFg', 'UCEzhyH0n4igPooUJOVcq-HQ', 'UCLvk76DFmbHIveAvYUDajUg', 'UCsr9eUfntn_WNKBdPGjhFNA', 'UCwyR-5gp7NCd-2DwLtdCtcw', 'UCbK636ZR5BdUIrEcu6YOCRw', 'UChYUp6gv-SWom7oIdPfrzaA', 'UCoARIsEr0lu7FLN6DfYk3TA', 'UCrf62gEqaGK2saKj_oU5IYg', 'UCKOwDvsF9Mp5FSgLxh5qIag', 'UCmV6YFTsQZ9_TK7kzrguFpA', 'UCTjEBVjiOTsXQUqbJvi59kg', 'UCJNqzcBpWK3Gt6IE1MxRr_Q', 'UCmpgyQt41fRttTKavambewA', 'UCtvF3qOM4qN3HKhDBt6Nhmw', 'UCwObifbiqZvhDm6emfp_vJQ', 'UCQxEEU1kq846WwLyXHxMY7A', 'UCJjwunfIpTvVsJrWIeiprlA', 'UC66diRcDsDtXqFffHD3zcVQ', 'UC9A3neTclGQxmPI9kAqx9jw', 'UCZqFAE6-5539HTem8cyfQuA', 'UCKVJ1f8j-Wz3LMSbiHi4DLQ', 'UCiMoJJB8OYePXFso2jSscYA', 'UCHVQjs3d-SmRuFtJurp84QQ', 'UCI52io2NXrmHjXpVB3sVbDg', 'UCMFpzGDVsTdOHDiLMHLSl7A', 'UCWohPFGHNprYwPOwvKlUxyQ', 'UCRN8qGSgGekQvtBrxU6Jt2g', 'UC6br5Obl00fe-p7vaNebPUQ', 'UCQp3vsLMn9WlF_4aSIHEEoQ', 'UCppnnruco5U5IPsQZIo7s0A', 'UCSWHUmhm8XuNp1UEz_p0BFQ', 'UC14xDOlecETvjL2by20FXrQ', 'UCYieht3paO1nFDXim5KZnbg', 'UCH6j6f4vxSlpeJGZCbPoePQ', 'UCo9OPeVJL5hgPtwxUTEBgSA', 'UCYZ7xx4T6Fq2ErsMrtadBHA', 'UCzYB6YA5f-Tc7GQcIese7pg', 'UCvpD0KP2b7nVLbEAydjjNaQ', 'UCmKTebUnJbeWuhUHSxsEDhQ', 'UC00DJ04oplqj4IUUB5vSwZw', 'UCiL9JJtFwbQsPDeHADSXstA', 'UCzP3gUCvOD22keyM9nKLpFg', 'UChr2Yvl1kepJWL2Q8sX2Udg', 'UCMJiRC8ebr3BM1bqSGy3lXA', 'UCtZ8IklGLW-aXp_bq7BrPzw', 'UCiAzDHGJTIjlXZZKj9aErWw', 'UCBt2y4jx0JJ0Bt4dMssVM-w', 'UCFmfq1jsqJ8Zp0zMdFQ8Vmw', 'UCR19aHW_92TAKGLoTH01Z7w', 'UCGhRiaKgkLlvPoBulWhX4gQ', 'UCWW_CFV7822ZhZjM9qEzupw', 'UCaN2hWDtZZ15Jt9HdntN2tw', 'UCCdCh7qLb-NR3kk8VTFyqig', 'UCrePMOPfWqU6nviA3gO1bXw', 'UCC-l8WDpZtqymNu1kssjY3g', 'UCHRS52TjwxpKz_VRKPGQ0pA', 'UCNKrDQQ9OLARlFVpHIi7nrQ', 'UCv6nXR8A-wSidnF6H-2wQYg', 'UCLgVu6xVfWfYnff1HoO8Lww', 'UCFYxrZHbGiZDxL6m8TZ30Qg', 'UC9Z-KxdMBq8G1xypxuCS7oQ', 'UClHKXblEdD7mGFOjX_ZJH3w', 'UCPDYF8wq8Arz4klmZNY2WRg', 'UCzAcA3VaroUsvdsQRXunttQ', 'UCP1bftsnaFPO0YoDYqgNCSA', 'UCkLbyx7Un3yN359hKXKYDCA', 'UCv2elfnDe8QqdLg219wlWHA', 'UCJUKgdi5lCQIzog55pCevIA', 'UCVyh4vbrB5cWnQWWAvGSinw', 'UCA_gbEJjpoO8qpf7hpyW0rA', 'UCj4C2AquQ1yrZ-70JN1xBTw', 'UCQ5XA58BhMpulMECLydOAxg', 'UCnekLiljel-Px4ClMC7b3mg', 'UCgCxYP5uSCNyFTV-PEbKhew', 'UCO-7CJCtOqw1yqh3y8owGfg', 'UCUrCIBJ3ScRAOLgPElscZqA', 'UCSx-2fuyotB8WA8KytyhACg', 'UCmPkZXhVfyLLWyHQM-l_KqA', 'UClsaLJyAdDlXjyAizmKt-1Q', 'UCGN0_2kvsOwdwbJq5q3SVGQ', 'UCrNISLWm4d6SRf8AUjoGm1g', 'UC0awE5h5rIOFh52li-lZObg', 'UCeMVG_xsUh7wJEHAic4G4AA', 'UCAzbl-HcJdvFy6oVRmJJQ1A', 'UC8D8Zn4iOnfng75AffMRuPg', 'UCqxtyL5WX9bvnXdpcWA9yzw', 'UC7R377JtSnWUAH3bIDX3mZw', 'UCYdYEVp2t0zD5xJu0hKWAgw', 'UChLr0rJAhEZZTUKT577QECA', 'UCZ-qOijZTB-rZRFkv2sJppA', 'UCkWDyNmU0TqhvD0g7yC5r2g', 'UCvD7HYdnFzBXaicx3LxRvCw', 'UC2bN1vE7esxNXhBSYIHzQwg', 'UC8-Waog35DgpfveQcw6U5cg');


-- ============================================================
-- [요청 2] 크리에이터 상세 통계
-- 목적: 크리에이터 성과 분석, 버블차트, 효율 매트릭스
-- 저장: youtuber_stats.csv
-- ============================================================
SELECT
    ys.channel_id,
    ys.average_views,
    ys.average_views_ads,
    ys.average_views_except_short,
    ys.average_views_short,
    ys.engagement_rate,
    ys.engagement_rate_last_10,
    ys.subs_growth_3_months,
    ys.subs_growth_3_months_amount,
    ys.short_ratio,
    ys.total_videos,
    ys.trend_count,
    ys.format1_long,
    ys.format1_short,
    ys.topic1_long,
    ys.topic1_short,
    ys.topic2_long,
    ys.topic2_short
FROM youtuber_stats ys
WHERE ys.channel_id IN ('UCwtLb11h7aai6EVcdwdlVJA', 'UCBoQ8_HIOVbOA_FuYtTapqA', 'UCRiIf6rt91BVfZVtURRXlOw', 'UCBlIcpkzSdcmp5G0XS7UsZA', 'UCff7sQ_kjCEPZvr8h8US8ww', 'UCun4wV8czkKcdMn_NDX8MIQ', 'UCfM7HC0wkS_cWVIcgpy2XPA', 'UCZ75Bt8hZt1AO2zRw36QJHw', 'UC26RKCp5GM9XxygDjikvtxw', 'UC4bNn3K-ivge2a_etU2jP9A', 'UCVRAHN1wuI9pUDyeSAc_I1A', 'UCM3LKBTSr8fUivTfrvOPZCg', 'UCvKl2U_gJeXRYGJKecvPcYA', 'UCA5CvI96Q7XtiRIxmajRzWw', 'UCPur_FJRVR-vKvAz1xvwq6w', 'UCx0ZL5ldCGMqkOGqyO1qOkw', 'UCkh6TlSape86-iHiehXvsmA', 'UCZCvbWrBFGQeZwf5qczqLFg', 'UCEzhyH0n4igPooUJOVcq-HQ', 'UCLvk76DFmbHIveAvYUDajUg', 'UCsr9eUfntn_WNKBdPGjhFNA', 'UCwyR-5gp7NCd-2DwLtdCtcw', 'UCbK636ZR5BdUIrEcu6YOCRw', 'UChYUp6gv-SWom7oIdPfrzaA', 'UCoARIsEr0lu7FLN6DfYk3TA', 'UCrf62gEqaGK2saKj_oU5IYg', 'UCKOwDvsF9Mp5FSgLxh5qIag', 'UCmV6YFTsQZ9_TK7kzrguFpA', 'UCTjEBVjiOTsXQUqbJvi59kg', 'UCJNqzcBpWK3Gt6IE1MxRr_Q', 'UCmpgyQt41fRttTKavambewA', 'UCtvF3qOM4qN3HKhDBt6Nhmw', 'UCwObifbiqZvhDm6emfp_vJQ', 'UCQxEEU1kq846WwLyXHxMY7A', 'UCJjwunfIpTvVsJrWIeiprlA', 'UC66diRcDsDtXqFffHD3zcVQ', 'UC9A3neTclGQxmPI9kAqx9jw', 'UCZqFAE6-5539HTem8cyfQuA', 'UCKVJ1f8j-Wz3LMSbiHi4DLQ', 'UCiMoJJB8OYePXFso2jSscYA', 'UCHVQjs3d-SmRuFtJurp84QQ', 'UCI52io2NXrmHjXpVB3sVbDg', 'UCMFpzGDVsTdOHDiLMHLSl7A', 'UCWohPFGHNprYwPOwvKlUxyQ', 'UCRN8qGSgGekQvtBrxU6Jt2g', 'UC6br5Obl00fe-p7vaNebPUQ', 'UCQp3vsLMn9WlF_4aSIHEEoQ', 'UCppnnruco5U5IPsQZIo7s0A', 'UCSWHUmhm8XuNp1UEz_p0BFQ', 'UC14xDOlecETvjL2by20FXrQ', 'UCYieht3paO1nFDXim5KZnbg', 'UCH6j6f4vxSlpeJGZCbPoePQ', 'UCo9OPeVJL5hgPtwxUTEBgSA', 'UCYZ7xx4T6Fq2ErsMrtadBHA', 'UCzYB6YA5f-Tc7GQcIese7pg', 'UCvpD0KP2b7nVLbEAydjjNaQ', 'UCmKTebUnJbeWuhUHSxsEDhQ', 'UC00DJ04oplqj4IUUB5vSwZw', 'UCiL9JJtFwbQsPDeHADSXstA', 'UCzP3gUCvOD22keyM9nKLpFg', 'UChr2Yvl1kepJWL2Q8sX2Udg', 'UCMJiRC8ebr3BM1bqSGy3lXA', 'UCtZ8IklGLW-aXp_bq7BrPzw', 'UCiAzDHGJTIjlXZZKj9aErWw', 'UCBt2y4jx0JJ0Bt4dMssVM-w', 'UCFmfq1jsqJ8Zp0zMdFQ8Vmw', 'UCR19aHW_92TAKGLoTH01Z7w', 'UCGhRiaKgkLlvPoBulWhX4gQ', 'UCWW_CFV7822ZhZjM9qEzupw', 'UCaN2hWDtZZ15Jt9HdntN2tw', 'UCCdCh7qLb-NR3kk8VTFyqig', 'UCrePMOPfWqU6nviA3gO1bXw', 'UCC-l8WDpZtqymNu1kssjY3g', 'UCHRS52TjwxpKz_VRKPGQ0pA', 'UCNKrDQQ9OLARlFVpHIi7nrQ', 'UCv6nXR8A-wSidnF6H-2wQYg', 'UCLgVu6xVfWfYnff1HoO8Lww', 'UCFYxrZHbGiZDxL6m8TZ30Qg', 'UC9Z-KxdMBq8G1xypxuCS7oQ', 'UClHKXblEdD7mGFOjX_ZJH3w', 'UCPDYF8wq8Arz4klmZNY2WRg', 'UCzAcA3VaroUsvdsQRXunttQ', 'UCP1bftsnaFPO0YoDYqgNCSA', 'UCkLbyx7Un3yN359hKXKYDCA', 'UCv2elfnDe8QqdLg219wlWHA', 'UCJUKgdi5lCQIzog55pCevIA', 'UCVyh4vbrB5cWnQWWAvGSinw', 'UCA_gbEJjpoO8qpf7hpyW0rA', 'UCj4C2AquQ1yrZ-70JN1xBTw', 'UCQ5XA58BhMpulMECLydOAxg', 'UCnekLiljel-Px4ClMC7b3mg', 'UCgCxYP5uSCNyFTV-PEbKhew', 'UCO-7CJCtOqw1yqh3y8owGfg', 'UCUrCIBJ3ScRAOLgPElscZqA', 'UCSx-2fuyotB8WA8KytyhACg', 'UCmPkZXhVfyLLWyHQM-l_KqA', 'UClsaLJyAdDlXjyAizmKt-1Q', 'UCGN0_2kvsOwdwbJq5q3SVGQ', 'UCrNISLWm4d6SRf8AUjoGm1g', 'UC0awE5h5rIOFh52li-lZObg', 'UCeMVG_xsUh7wJEHAic4G4AA', 'UCAzbl-HcJdvFy6oVRmJJQ1A', 'UC8D8Zn4iOnfng75AffMRuPg', 'UCqxtyL5WX9bvnXdpcWA9yzw', 'UC7R377JtSnWUAH3bIDX3mZw', 'UCYdYEVp2t0zD5xJu0hKWAgw', 'UChLr0rJAhEZZTUKT577QECA', 'UCZ-qOijZTB-rZRFkv2sJppA', 'UCkWDyNmU0TqhvD0g7yC5r2g', 'UCvD7HYdnFzBXaicx3LxRvCw', 'UC2bN1vE7esxNXhBSYIHzQwg', 'UC8-Waog35DgpfveQcw6U5cg');


-- ============================================================
-- [요청 3] 시청자 인구통계 (성별 x 연령대)
-- 목적: 오디언스 인사이트, 인구 피라미드
-- 저장: demography.csv
-- ============================================================
SELECT
    d.channel_id,
    d.F13_17,
    d.F18_24,
    d.F25_34,
    d.F35_44,
    d.F45_54,
    d.F55_64,
    d.F65,
    d.M13_17,
    d.M18_24,
    d.M25_34,
    d.M35_44,
    d.M45_54,
    d.M55_64,
    d.M65
FROM demography d
WHERE d.channel_id IN ('UCwtLb11h7aai6EVcdwdlVJA', 'UCBoQ8_HIOVbOA_FuYtTapqA', 'UCRiIf6rt91BVfZVtURRXlOw', 'UCBlIcpkzSdcmp5G0XS7UsZA', 'UCff7sQ_kjCEPZvr8h8US8ww', 'UCun4wV8czkKcdMn_NDX8MIQ', 'UCfM7HC0wkS_cWVIcgpy2XPA', 'UCZ75Bt8hZt1AO2zRw36QJHw', 'UC26RKCp5GM9XxygDjikvtxw', 'UC4bNn3K-ivge2a_etU2jP9A', 'UCVRAHN1wuI9pUDyeSAc_I1A', 'UCM3LKBTSr8fUivTfrvOPZCg', 'UCvKl2U_gJeXRYGJKecvPcYA', 'UCA5CvI96Q7XtiRIxmajRzWw', 'UCPur_FJRVR-vKvAz1xvwq6w', 'UCx0ZL5ldCGMqkOGqyO1qOkw', 'UCkh6TlSape86-iHiehXvsmA', 'UCZCvbWrBFGQeZwf5qczqLFg', 'UCEzhyH0n4igPooUJOVcq-HQ', 'UCLvk76DFmbHIveAvYUDajUg', 'UCsr9eUfntn_WNKBdPGjhFNA', 'UCwyR-5gp7NCd-2DwLtdCtcw', 'UCbK636ZR5BdUIrEcu6YOCRw', 'UChYUp6gv-SWom7oIdPfrzaA', 'UCoARIsEr0lu7FLN6DfYk3TA', 'UCrf62gEqaGK2saKj_oU5IYg', 'UCKOwDvsF9Mp5FSgLxh5qIag', 'UCmV6YFTsQZ9_TK7kzrguFpA', 'UCTjEBVjiOTsXQUqbJvi59kg', 'UCJNqzcBpWK3Gt6IE1MxRr_Q', 'UCmpgyQt41fRttTKavambewA', 'UCtvF3qOM4qN3HKhDBt6Nhmw', 'UCwObifbiqZvhDm6emfp_vJQ', 'UCQxEEU1kq846WwLyXHxMY7A', 'UCJjwunfIpTvVsJrWIeiprlA', 'UC66diRcDsDtXqFffHD3zcVQ', 'UC9A3neTclGQxmPI9kAqx9jw', 'UCZqFAE6-5539HTem8cyfQuA', 'UCKVJ1f8j-Wz3LMSbiHi4DLQ', 'UCiMoJJB8OYePXFso2jSscYA', 'UCHVQjs3d-SmRuFtJurp84QQ', 'UCI52io2NXrmHjXpVB3sVbDg', 'UCMFpzGDVsTdOHDiLMHLSl7A', 'UCWohPFGHNprYwPOwvKlUxyQ', 'UCRN8qGSgGekQvtBrxU6Jt2g', 'UC6br5Obl00fe-p7vaNebPUQ', 'UCQp3vsLMn9WlF_4aSIHEEoQ', 'UCppnnruco5U5IPsQZIo7s0A', 'UCSWHUmhm8XuNp1UEz_p0BFQ', 'UC14xDOlecETvjL2by20FXrQ', 'UCYieht3paO1nFDXim5KZnbg', 'UCH6j6f4vxSlpeJGZCbPoePQ', 'UCo9OPeVJL5hgPtwxUTEBgSA', 'UCYZ7xx4T6Fq2ErsMrtadBHA', 'UCzYB6YA5f-Tc7GQcIese7pg', 'UCvpD0KP2b7nVLbEAydjjNaQ', 'UCmKTebUnJbeWuhUHSxsEDhQ', 'UC00DJ04oplqj4IUUB5vSwZw', 'UCiL9JJtFwbQsPDeHADSXstA', 'UCzP3gUCvOD22keyM9nKLpFg', 'UChr2Yvl1kepJWL2Q8sX2Udg', 'UCMJiRC8ebr3BM1bqSGy3lXA', 'UCtZ8IklGLW-aXp_bq7BrPzw', 'UCiAzDHGJTIjlXZZKj9aErWw', 'UCBt2y4jx0JJ0Bt4dMssVM-w', 'UCFmfq1jsqJ8Zp0zMdFQ8Vmw', 'UCR19aHW_92TAKGLoTH01Z7w', 'UCGhRiaKgkLlvPoBulWhX4gQ', 'UCWW_CFV7822ZhZjM9qEzupw', 'UCaN2hWDtZZ15Jt9HdntN2tw', 'UCCdCh7qLb-NR3kk8VTFyqig', 'UCrePMOPfWqU6nviA3gO1bXw', 'UCC-l8WDpZtqymNu1kssjY3g', 'UCHRS52TjwxpKz_VRKPGQ0pA', 'UCNKrDQQ9OLARlFVpHIi7nrQ', 'UCv6nXR8A-wSidnF6H-2wQYg', 'UCLgVu6xVfWfYnff1HoO8Lww', 'UCFYxrZHbGiZDxL6m8TZ30Qg', 'UC9Z-KxdMBq8G1xypxuCS7oQ', 'UClHKXblEdD7mGFOjX_ZJH3w', 'UCPDYF8wq8Arz4klmZNY2WRg', 'UCzAcA3VaroUsvdsQRXunttQ', 'UCP1bftsnaFPO0YoDYqgNCSA', 'UCkLbyx7Un3yN359hKXKYDCA', 'UCv2elfnDe8QqdLg219wlWHA', 'UCJUKgdi5lCQIzog55pCevIA', 'UCVyh4vbrB5cWnQWWAvGSinw', 'UCA_gbEJjpoO8qpf7hpyW0rA', 'UCj4C2AquQ1yrZ-70JN1xBTw', 'UCQ5XA58BhMpulMECLydOAxg', 'UCnekLiljel-Px4ClMC7b3mg', 'UCgCxYP5uSCNyFTV-PEbKhew', 'UCO-7CJCtOqw1yqh3y8owGfg', 'UCUrCIBJ3ScRAOLgPElscZqA', 'UCSx-2fuyotB8WA8KytyhACg', 'UCmPkZXhVfyLLWyHQM-l_KqA', 'UClsaLJyAdDlXjyAizmKt-1Q', 'UCGN0_2kvsOwdwbJq5q3SVGQ', 'UCrNISLWm4d6SRf8AUjoGm1g', 'UC0awE5h5rIOFh52li-lZObg', 'UCeMVG_xsUh7wJEHAic4G4AA', 'UCAzbl-HcJdvFy6oVRmJJQ1A', 'UC8D8Zn4iOnfng75AffMRuPg', 'UCqxtyL5WX9bvnXdpcWA9yzw', 'UC7R377JtSnWUAH3bIDX3mZw', 'UCYdYEVp2t0zD5xJu0hKWAgw', 'UChLr0rJAhEZZTUKT577QECA', 'UCZ-qOijZTB-rZRFkv2sJppA', 'UCkWDyNmU0TqhvD0g7yC5r2g', 'UCvD7HYdnFzBXaicx3LxRvCw', 'UC2bN1vE7esxNXhBSYIHzQwg', 'UC8-Waog35DgpfveQcw6U5cg');


-- ============================================================
-- [요청 4] 브랜드 기본 정보 (뷰티 관련 전체)
-- 목적: 절대적 시장 순위 (brand_logo_beauty 기반)
-- 저장: brand_logo_beauty.csv
-- ※ 이 쿼리는 브랜드 공통 - 다른 브랜드와 동일한 결과
-- ============================================================
SELECT
    bl.brand_logo_id,
    bl.brand_name_kr,
    bl.brand_name_en,
    bl.brand_videos,
    bl.avg_views,
    bl.one_month,
    bl.topic,
    bl.related_brands
FROM brand_logo bl
WHERE bl.topic LIKE '%beauty%'
   OR bl.topic LIKE '%makeup%'
   OR bl.topic LIKE '%cosmetic%'
   OR bl.topic LIKE '%뷰티%'
   OR bl.topic LIKE '%메이크업%'
   OR bl.topic LIKE '%화장%';


-- ============================================================
-- [요청 5] 크리에이터 프로필 정보
-- 목적: 크리에이터 카드, 채널 기본 정보
-- 저장: youtuber_info.csv
-- ============================================================
SELECT
    yi.channel_id,
    yi.title,
    yi.subscribers,
    yi.totalViews,
    yi.totalVideos,
    yi.thumbnail,
    yi.categories,
    yi.channel_type,
    yi.Main_tag1,
    yi.Main_tag2,
    yi.email,
    yi.channel_cost,
    yi.upload_cycle
FROM youtuber_info yi
WHERE yi.channel_id IN ('UCwtLb11h7aai6EVcdwdlVJA', 'UCBoQ8_HIOVbOA_FuYtTapqA', 'UCRiIf6rt91BVfZVtURRXlOw', 'UCBlIcpkzSdcmp5G0XS7UsZA', 'UCff7sQ_kjCEPZvr8h8US8ww', 'UCun4wV8czkKcdMn_NDX8MIQ', 'UCfM7HC0wkS_cWVIcgpy2XPA', 'UCZ75Bt8hZt1AO2zRw36QJHw', 'UC26RKCp5GM9XxygDjikvtxw', 'UC4bNn3K-ivge2a_etU2jP9A', 'UCVRAHN1wuI9pUDyeSAc_I1A', 'UCM3LKBTSr8fUivTfrvOPZCg', 'UCvKl2U_gJeXRYGJKecvPcYA', 'UCA5CvI96Q7XtiRIxmajRzWw', 'UCPur_FJRVR-vKvAz1xvwq6w', 'UCx0ZL5ldCGMqkOGqyO1qOkw', 'UCkh6TlSape86-iHiehXvsmA', 'UCZCvbWrBFGQeZwf5qczqLFg', 'UCEzhyH0n4igPooUJOVcq-HQ', 'UCLvk76DFmbHIveAvYUDajUg', 'UCsr9eUfntn_WNKBdPGjhFNA', 'UCwyR-5gp7NCd-2DwLtdCtcw', 'UCbK636ZR5BdUIrEcu6YOCRw', 'UChYUp6gv-SWom7oIdPfrzaA', 'UCoARIsEr0lu7FLN6DfYk3TA', 'UCrf62gEqaGK2saKj_oU5IYg', 'UCKOwDvsF9Mp5FSgLxh5qIag', 'UCmV6YFTsQZ9_TK7kzrguFpA', 'UCTjEBVjiOTsXQUqbJvi59kg', 'UCJNqzcBpWK3Gt6IE1MxRr_Q', 'UCmpgyQt41fRttTKavambewA', 'UCtvF3qOM4qN3HKhDBt6Nhmw', 'UCwObifbiqZvhDm6emfp_vJQ', 'UCQxEEU1kq846WwLyXHxMY7A', 'UCJjwunfIpTvVsJrWIeiprlA', 'UC66diRcDsDtXqFffHD3zcVQ', 'UC9A3neTclGQxmPI9kAqx9jw', 'UCZqFAE6-5539HTem8cyfQuA', 'UCKVJ1f8j-Wz3LMSbiHi4DLQ', 'UCiMoJJB8OYePXFso2jSscYA', 'UCHVQjs3d-SmRuFtJurp84QQ', 'UCI52io2NXrmHjXpVB3sVbDg', 'UCMFpzGDVsTdOHDiLMHLSl7A', 'UCWohPFGHNprYwPOwvKlUxyQ', 'UCRN8qGSgGekQvtBrxU6Jt2g', 'UC6br5Obl00fe-p7vaNebPUQ', 'UCQp3vsLMn9WlF_4aSIHEEoQ', 'UCppnnruco5U5IPsQZIo7s0A', 'UCSWHUmhm8XuNp1UEz_p0BFQ', 'UC14xDOlecETvjL2by20FXrQ', 'UCYieht3paO1nFDXim5KZnbg', 'UCH6j6f4vxSlpeJGZCbPoePQ', 'UCo9OPeVJL5hgPtwxUTEBgSA', 'UCYZ7xx4T6Fq2ErsMrtadBHA', 'UCzYB6YA5f-Tc7GQcIese7pg', 'UCvpD0KP2b7nVLbEAydjjNaQ', 'UCmKTebUnJbeWuhUHSxsEDhQ', 'UC00DJ04oplqj4IUUB5vSwZw', 'UCiL9JJtFwbQsPDeHADSXstA', 'UCzP3gUCvOD22keyM9nKLpFg', 'UChr2Yvl1kepJWL2Q8sX2Udg', 'UCMJiRC8ebr3BM1bqSGy3lXA', 'UCtZ8IklGLW-aXp_bq7BrPzw', 'UCiAzDHGJTIjlXZZKj9aErWw', 'UCBt2y4jx0JJ0Bt4dMssVM-w', 'UCFmfq1jsqJ8Zp0zMdFQ8Vmw', 'UCR19aHW_92TAKGLoTH01Z7w', 'UCGhRiaKgkLlvPoBulWhX4gQ', 'UCWW_CFV7822ZhZjM9qEzupw', 'UCaN2hWDtZZ15Jt9HdntN2tw', 'UCCdCh7qLb-NR3kk8VTFyqig', 'UCrePMOPfWqU6nviA3gO1bXw', 'UCC-l8WDpZtqymNu1kssjY3g', 'UCHRS52TjwxpKz_VRKPGQ0pA', 'UCNKrDQQ9OLARlFVpHIi7nrQ', 'UCv6nXR8A-wSidnF6H-2wQYg', 'UCLgVu6xVfWfYnff1HoO8Lww', 'UCFYxrZHbGiZDxL6m8TZ30Qg', 'UC9Z-KxdMBq8G1xypxuCS7oQ', 'UClHKXblEdD7mGFOjX_ZJH3w', 'UCPDYF8wq8Arz4klmZNY2WRg', 'UCzAcA3VaroUsvdsQRXunttQ', 'UCP1bftsnaFPO0YoDYqgNCSA', 'UCkLbyx7Un3yN359hKXKYDCA', 'UCv2elfnDe8QqdLg219wlWHA', 'UCJUKgdi5lCQIzog55pCevIA', 'UCVyh4vbrB5cWnQWWAvGSinw', 'UCA_gbEJjpoO8qpf7hpyW0rA', 'UCj4C2AquQ1yrZ-70JN1xBTw', 'UCQ5XA58BhMpulMECLydOAxg', 'UCnekLiljel-Px4ClMC7b3mg', 'UCgCxYP5uSCNyFTV-PEbKhew', 'UCO-7CJCtOqw1yqh3y8owGfg', 'UCUrCIBJ3ScRAOLgPElscZqA', 'UCSx-2fuyotB8WA8KytyhACg', 'UCmPkZXhVfyLLWyHQM-l_KqA', 'UClsaLJyAdDlXjyAizmKt-1Q', 'UCGN0_2kvsOwdwbJq5q3SVGQ', 'UCrNISLWm4d6SRf8AUjoGm1g', 'UC0awE5h5rIOFh52li-lZObg', 'UCeMVG_xsUh7wJEHAic4G4AA', 'UCAzbl-HcJdvFy6oVRmJJQ1A', 'UC8D8Zn4iOnfng75AffMRuPg', 'UCqxtyL5WX9bvnXdpcWA9yzw', 'UC7R377JtSnWUAH3bIDX3mZw', 'UCYdYEVp2t0zD5xJu0hKWAgw', 'UChLr0rJAhEZZTUKT577QECA', 'UCZ-qOijZTB-rZRFkv2sJppA', 'UCkWDyNmU0TqhvD0g7yC5r2g', 'UCvD7HYdnFzBXaicx3LxRvCw', 'UC2bN1vE7esxNXhBSYIHzQwg', 'UC8-Waog35DgpfveQcw6U5cg');


-- ============================================================
-- [요청 6] 올리브영 브랜드 스코어 추이
-- 목적: 브랜드 스코어 트렌드 차트
-- 저장: oliveyoung_brand_score.csv
-- brand ID: LG생활건강(112), 메디큐브(4002), 라네즈(80), 이니스프리(63),
--           에스트라(79), 설화수(119), 정샘물(78449), 덴티스테(4516), 케라스타즈(61511)
-- ============================================================
SELECT
    obs.brand,
    obs.brand_score,
    obs.brand_rank_score,
    obs.brand_related_video_score,
    obs.date
FROM oliveyoung_brand_score obs
WHERE obs.brand IN (112, 4002, 80, 63, 79, 119, 78449, 4516, 61511)
ORDER BY obs.date DESC;


-- ============================================================
-- [요청 7] 올리브영 제품 순위 변동
-- 목적: 제품 랭킹 트렌드
-- 저장: oliveyoung_product_rank.csv
-- brand ID: LG생활건강(112), 메디큐브(4002), 라네즈(80), 이니스프리(63),
--           에스트라(79), 설화수(119), 정샘물(78449), 덴티스테(4516), 케라스타즈(61511)
-- ============================================================
SELECT
    opr.product_id,
    opr.category,
    opr.rank AS product_rank,
    opr.score,
    opr.date,
    opr.momentum_direction,
    opr.rank_avg_7d
FROM oliveyoung_product_agg_rank_daily opr
WHERE opr.product_id IN (
    SELECT opi.product_id
    FROM oliveyoung_product_info opi
    WHERE opi.brand IN ('LG생활건강', '메디큐브', '라네즈', '이니스프리', '에스트라', '설화수', '정샘물', '덴티스테', '케라스타즈')
)
ORDER BY opr.date DESC, opr.rank ASC;


-- ============================================================
-- [요청 8] 올리브영 제품 정보
-- 목적: 제품 카드 표시
-- 저장: oliveyoung_product_info.csv
-- ============================================================
SELECT
    opi.product_id,
    opi.brand,
    opi.product,
    opi.category,
    opi.image
FROM oliveyoung_product_info opi
WHERE opi.brand IN ('LG생활건강', '메디큐브', '라네즈', '이니스프리', '에스트라', '설화수', '정샘물', '덴티스테', '케라스타즈');
