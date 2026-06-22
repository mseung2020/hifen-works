"""
릴스/피드 분리 + 날짜 결합 — Branch & Bound 최적 탐색
  - 샘플 10%로 빠르게 탐색, 상위 결과를 전체 데이터로 검증
  - Branch & Bound: recall 불가능한 분기를 조기 차단하여 탐색 공간 축소

구조:
  릴스:  a.is_reel = 1 AND (a.views >= V1 OR a.likes >= L1 OR a.comments >= C1)
  피드:  a.is_reel = 0 AND ((b.followers >= F1 AND a.publish_date >= D1) OR a.likes >= L2 OR a.views >= V2)
"""

import pandas as pd
import numpy as np
import time, os, json, asyncio
from typing import Optional, Callable

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(BASE_DIR)
TOTAL_PATH = os.path.join(PARENT_DIR, "total_insta_id_slim.csv")
AD_PATH = os.path.join(PARENT_DIR, "ad_insta_id.csv")
SAVE_PATH = os.path.join(BASE_DIR, "analysis_result.json")


def build_verification_sql(where_clause: str, label: str = "") -> str:
    comment = f"-- [{label}]\n" if label else ""
    return (
        f"{comment}"
        f"WITH stats AS (\n"
        f"    SELECT \n"
        f"        COUNT(*) AS total_count,\n"
        f"        SUM(CASE WHEN ({where_clause}) THEN 1 ELSE 0 END) AS kept_count,\n"
        f"        SUM(CASE WHEN c.post_id IS NOT NULL THEN 1 ELSE 0 END) AS ad_total_count,\n"
        f"        SUM(CASE WHEN c.post_id IS NOT NULL\n"
        f"                  AND ({where_clause}) THEN 1 ELSE 0 END) AS ad_kept_count\n"
        f"    FROM hifen.instagram_post a\n"
        f"    LEFT JOIN hifen.instagram_user_stat b ON a.user_id = b.user_id\n"
        f"    LEFT JOIN (\n"
        f"        SELECT DISTINCT post_id \n"
        f"        FROM hifen.instagram_ppl_brand\n"
        f"    ) c ON a.post_id = c.post_id\n"
        f")\n"
        f"SELECT \n"
        f"    total_count AS '전체_데이터_수',\n"
        f"    kept_count AS '필터통과_데이터_수',\n"
        f"    ad_total_count AS '전체_광고_수(정답지)',\n"
        f"    ad_kept_count AS '필터통과_광고_수',\n"
        f"    CONCAT(ROUND((ad_kept_count / ad_total_count) * 100, 2), '%') AS '리콜_Recall(%)',\n"
        f"    CONCAT(ROUND(((total_count - kept_count) / total_count) * 100, 2), '%') AS '제거율_Removal(%)'\n"
        f"FROM stats;"
    )


class ReelSplitEngine:
    """릴스/피드 분리 + 날짜 Branch & Bound 엔진"""

    def __init__(self):
        self.df = None
        self.results = []
        self.status = "idle"
        self.progress = 0
        self._broadcast: Optional[Callable] = None
        self._log_history = []

    def set_broadcast(self, fn):
        self._broadcast = fn

    async def _send(self, msg_type: str, data: dict):
        payload = {"type": msg_type, **data}
        self._log_history.append(payload)
        if self._broadcast:
            await self._broadcast(json.dumps(payload, ensure_ascii=False, default=str))

    async def _send_status(self, status: str, progress: int, detail: str = ""):
        self.status = status
        self.progress = progress
        await self._send("status", {"status": status, "progress": progress, "detail": detail})

    # ─── 데이터 로드 ───
    async def load_data(self):
        await self._send_status("loading", 0, "데이터 로드 시작...")
        t0 = time.time()

        self.df = pd.read_csv(
            TOTAL_PATH, sep=";",
            usecols=["post_id", "is_reel", "views", "likes", "comments", "followers", "publish_date"],
            dtype={"post_id": "str", "is_reel": "int8",
                   "views": "int32", "likes": "int32", "comments": "int32",
                   "followers": "int32", "publish_date": "str"},
        )
        await self._send_status("loading", 25, f"로드 완료: {len(self.df):,}건")

        ad = pd.read_csv(AD_PATH, sep=";", quotechar='"',
                         usecols=["post_id"], dtype={"post_id": "str"})
        self.df["is_ad"] = self.df["post_id"].isin(set(ad["post_id"])).astype("int8")
        del ad

        n_total = len(self.df)
        n_ad = (self.df["is_ad"] == 1).sum()

        await self._send_status("loaded", 35,
            f"데이터 준비 완료: 전체 {n_total:,}건 / 광고 {n_ad:,}건 ({time.time()-t0:.1f}s)")
        await self._send("data_summary", {
            "total": n_total, "ad": int(n_ad),
            "normal": int(n_total - n_ad),
            "reel": int((self.df["is_reel"] == 1).sum()),
            "post": int((self.df["is_reel"] == 0).sum()),
        })

    # ─── Branch & Bound 탐색 ───
    async def search(self):
        await self._send_status("simulating", 40, "샘플 생성 + 사전 계산 중...")

        # ── 전체 배열 (검증용) ──
        full_views = self.df["views"].values
        full_likes = self.df["likes"].values
        full_comments = self.df["comments"].values
        full_followers = self.df["followers"].values
        full_is_reel = self.df["is_reel"].values
        full_ad_mask = self.df["is_ad"].values == 1
        full_dates = pd.to_datetime(self.df["publish_date"], errors="coerce").values
        N = len(self.df)
        N_AD = full_ad_mask.sum()

        # ── 10% 샘플 생성 ──
        ad_idx = np.where(full_ad_mask)[0]
        normal_idx = np.where(~full_ad_mask)[0]
        np.random.seed(42)
        sample_normal = np.random.choice(normal_idx, size=len(normal_idx) // 10, replace=False)
        sidx = np.sort(np.concatenate([ad_idx, sample_normal]))

        views = full_views[sidx]
        likes = full_likes[sidx]
        comments = full_comments[sidx]
        followers = full_followers[sidx]
        is_reel = full_is_reel[sidx]
        ad_mask = self.df["is_ad"].values[sidx] == 1
        dates = full_dates[sidx]
        S_N = len(sidx)
        S_N_AD = ad_mask.sum()

        reel_mask = is_reel == 1
        feed_mask = is_reel == 0

        # 광고 중 릴스/피드 수
        reel_ad_mask = ad_mask & reel_mask
        feed_ad_mask = ad_mask & feed_mask
        reel_ad_n = reel_ad_mask.sum()
        feed_ad_n = feed_ad_mask.sum()

        await self._send_status("simulating", 45,
            f"샘플 {S_N:,}건 (광고: 릴스 {reel_ad_n:,} + 피드 {feed_ad_n:,})")

        # ── 후보값 정의 ──
        ad_v = views[ad_mask]
        ad_l = likes[ad_mask]
        ad_c = comments[ad_mask]
        ad_f = followers[ad_mask]

        # 광고 내 릴스/피드 마스크 (ad_mask 기준, 길이 = S_N_AD)
        ad_is_reel = is_reel[ad_mask]
        ad_reel = ad_is_reel == 1
        ad_feed = ad_is_reel == 0

        # 릴스 후보 (views, likes, comments)
        reel_v_vals = sorted(set(
            [0] + [int(np.percentile(ad_v[ad_reel], p)) for p in [1,3,5,10,25] if ad_reel.sum() > 0]
            + list(range(0, 10001, 1000))
        ))
        reel_l_vals = sorted(set(
            [0, 1, 3, 5, 10, 20, 50, 100, 200, 500]
        ))
        reel_c_vals = sorted(set(
            [0, 1, 3, 5, 10, 20, 50, 100]
        ))

        # 피드 후보 (followers, date, likes, views)
        feed_f_vals = sorted(set(
            [0] + [int(np.percentile(ad_f[ad_feed], p)) for p in [1,3,5,10,25,50] if ad_feed.sum() > 0]
            + list(range(0, 20001, 2000))
        ))
        date_cuts = ["2025-07-01", "2025-01-01", "2024-07-01", "2024-01-01",
                     "2023-07-01", "2023-01-01", "2022-01-01"]
        feed_l_vals = sorted(set(
            [0, 1, 3, 5, 10, 20, 50, 100, 200, 500]
        ))
        feed_v_vals = sorted(set(
            [0] + list(range(0, 10001, 1000))
        ))

        reel_total = len(reel_v_vals) * len(reel_l_vals) * len(reel_c_vals)
        feed_total = len(feed_f_vals) * len(date_cuts) * len(feed_l_vals) * len(feed_v_vals)

        await self._send_status("simulating", 48,
            f"릴스 {len(reel_v_vals)}×{len(reel_l_vals)}×{len(reel_c_vals)}={reel_total:,} / "
            f"피드 {len(feed_f_vals)}×{len(date_cuts)}×{len(feed_l_vals)}×{len(feed_v_vals)}={feed_total:,} / "
            f"최대 {reel_total * feed_total:,} (Branch&Bound로 축소)")

        # ── 사전 캐싱 ──
        await self._send_status("simulating", 50, "마스크 사전 캐싱 중...")

        # 릴스 마스크 (릴스 데이터에만 적용)
        rv_masks = {v: reel_mask & (views >= v) for v in reel_v_vals}
        rl_masks = {l: reel_mask & (likes >= l) for l in reel_l_vals}
        rc_masks = {c: reel_mask & (comments >= c) for c in reel_c_vals}

        # 피드 마스크
        ff_masks = {f: feed_mask & (followers >= f) for f in feed_f_vals}
        fd_masks = {dc: dates >= np.datetime64(dc) for dc in date_cuts}
        fl_masks = {l: feed_mask & (likes >= l) for l in feed_l_vals}
        fv_masks = {v: feed_mask & (views >= v) for v in feed_v_vals}

        # 릴스 조합별 (keep_reel, reel_ad_kept) 사전 계산
        # → 릴스 결과를 캐싱하면 피드 루프에서 반복 계산 안 해도 됨
        await self._send_status("simulating", 52, "릴스 조합 사전 평가 중...")

        reel_combos = []  # (reel_keep, reel_ad_kept, v1, l1, c1)
        for v1 in reel_v_vals:
            for l1 in reel_l_vals:
                for c1 in reel_c_vals:
                    reel_keep = rv_masks[v1] | rl_masks[l1] | rc_masks[c1]
                    reel_ad_kept = reel_keep[ad_mask].sum()
                    reel_combos.append((reel_keep, reel_ad_kept, v1, l1, c1))

        # reel_ad_kept 내림차순 정렬 (더 많이 보존하는 릴스 조건부터)
        reel_combos.sort(key=lambda x: x[1], reverse=True)

        await self._send_status("simulating", 55,
            f"릴스 조합 {len(reel_combos):,}개 사전 평가 완료")

        # ── 피드 조합별 최대 가능 ad_kept 사전 계산 ──
        # 피드의 "가장 관대한 조건" = F>=0 AND D>=2022 OR L>=0 OR V>=0 → 피드 전체
        # 피드 광고 전수 = feed_ad_n
        # 따라서 피드의 최대 가능 recall 기여 = feed_ad_n / S_N_AD

        MIN_RECALL = 0.95
        min_ad_needed = int(np.ceil(S_N_AD * MIN_RECALL))

        # ── Branch & Bound 메인 루프 ──
        await self._send_status("simulating", 58, "Branch & Bound 탐색 시작...")

        combo_results = []
        best_drop = 0
        total_tried = 0
        total_skipped = 0
        total_found = 0

        # 이전 결과 로드
        prev_path = SAVE_PATH
        if os.path.exists(prev_path):
            with open(prev_path) as f:
                prev = json.load(f)
            if prev.get("all_results"):
                combo_results = prev["all_results"]
                total_found = len(combo_results)
                if combo_results:
                    best_drop = max(r.get("drop_rate", 0) for r in combo_results)
                await self._send_status("simulating", 58,
                    f"이전 결과 복원: {total_found:,}개, 최고 {best_drop*100:.1f}%")
                ranked = sorted([r for r in combo_results if r.get("drop_rate", 0) >= 0.20],
                                key=lambda x: x["drop_rate"], reverse=True)
                for r in ranked[:20]:
                    await self._send("combo_result", {
                        **r,
                        "recall_pct": round(r["recall"] * 100, 2),
                        "drop_pct": round(r["drop_rate"] * 100, 2),
                    })

        async def _emit(result):
            nonlocal best_drop, total_found
            total_found += 1
            combo_results.append(result)
            if result["drop_rate"] < 0.20:
                return
            if result["drop_rate"] > best_drop:
                best_drop = result["drop_rate"]
                await self._send("combo_result", {
                    **result,
                    "recall_pct": round(result["recall"] * 100, 2),
                    "drop_pct": round(result["drop_rate"] * 100, 2),
                })

        def _save_now():
            import datetime
            qualified = [r for r in combo_results if r.get("drop_rate", 0) >= 0.20]
            ranked = sorted(qualified, key=lambda x: x["drop_rate"], reverse=True)
            save_data = {
                "saved_at": datetime.datetime.now().isoformat(),
                "status": "in_progress",
                "total_tried": total_tried,
                "total_skipped": total_skipped,
                "total_found": total_found,
                "top20": ranked[:20],
                "all_results": combo_results,
                "log_history": self._log_history,
            }
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, default=str)

        t_start = time.time()

        for ri, (reel_keep, reel_ad_kept, v1, l1, c1) in enumerate(reel_combos):

            # ── Branch: 릴스만으로 recall 가능성 체크 ──
            # 릴스 ad + 피드 최대(=피드 광고 전수) >= 필요 최소?
            max_possible_ad = reel_ad_kept + feed_ad_n
            if max_possible_ad < min_ad_needed:
                # 이 릴스 조건은 아무리 피드가 좋아도 recall 95% 불가 → 전체 스킵
                total_skipped += feed_total
                continue

            # 릴스 조건으로 보존되는 전체 건수 (drop 계산용)
            reel_kept_total = reel_keep.sum()

            for f1 in feed_f_vals:
                for dc in date_cuts:
                    ff_dc = ff_masks[f1] & fd_masks[dc]

                    for l2 in feed_l_vals:
                        fl = fl_masks[l2]

                        # ── Bound: (F&D) + L 만으로도 recall 부족한지 체크 ──
                        # 피드 보존 = (F>=f1 AND D>=dc) OR (L>=l2) OR (V>=???)
                        # V=0이면 최대 보존 → 여기서도 recall 부족하면 V 루프 전체 스킵
                        feed_keep_max = ff_dc | fl | fv_masks[0]  # V>=0 = 피드 전체
                        feed_ad_max = feed_keep_max[ad_mask].sum()
                        total_ad_max = reel_ad_kept + feed_ad_max

                        if total_ad_max < min_ad_needed:
                            total_skipped += len(feed_v_vals)
                            continue

                        for v2 in feed_v_vals:
                            total_tried += 1

                            feed_keep = ff_dc | fl | fv_masks[v2]
                            keep = reel_keep | feed_keep

                            ad_kept = keep[ad_mask].sum()
                            recall = ad_kept / S_N_AD
                            if recall < MIN_RECALL:
                                continue

                            drop = 1 - keep.sum() / S_N

                            where = (
                                f"(a.is_reel = 1 AND (a.views >= {v1} OR a.likes >= {l1} OR a.comments >= {c1}))\n"
                                f"        OR\n"
                                f"        (a.is_reel = 0 AND (\n"
                                f"            (b.followers >= {f1} AND a.publish_date >= '{dc}')\n"
                                f"            OR a.likes >= {l2}\n"
                                f"            OR a.views >= {v2}\n"
                                f"        ))"
                            )

                            await _emit({
                                "method": "릴스+피드+날짜",
                                "condition": (
                                    f"릴스:V>={v1:,}|L>={l1}|C>={c1} / "
                                    f"피드:(F>={f1:,}&D>={dc})|L>={l2}|V>={v2:,}"
                                ),
                                "recall": round(float(recall), 4),
                                "drop_rate": round(float(drop), 4),
                                "ad_kept": int(ad_kept),
                                "total_kept": int(keep.sum()),
                                "sql": build_verification_sql(where, "릴스+피드+날짜"),
                            })

                    # 피드 l2/v2 루프 끝 — 주기적 진행률
                    if total_tried % 50000 < len(feed_v_vals) * len(feed_l_vals) * 2:
                        elapsed = time.time() - t_start
                        speed = total_tried / max(elapsed, 1)
                        pct = min(95, 58 + int(ri / len(reel_combos) * 37))
                        await self._send_status("simulating", pct,
                            f"[릴스+피드] 탐색 {total_tried:,} / 스킵 {total_skipped:,} / "
                            f"유효 {total_found:,} (최고 {best_drop*100:.1f}%) "
                            f"[{speed:,.0f}건/초]")
                        _save_now()

        _save_now()
        elapsed = time.time() - t_start
        await self._send_status("simulated", 96,
            f"샘플 탐색 완료! {total_tried:,}개 탐색 + {total_skipped:,}개 스킵 → "
            f"{total_found:,}개 유효 (최고 {best_drop*100:.1f}%, {elapsed:.0f}초)")

        self.results = combo_results

    # ─── 전체 데이터 검증 ───
    async def verify(self):
        await self._send_status("verifying", 96, "상위 200개를 전체 데이터로 검증 중...")

        views = self.df["views"].values
        likes = self.df["likes"].values
        comments = self.df["comments"].values
        followers = self.df["followers"].values
        is_reel = self.df["is_reel"].values
        ad_mask = self.df["is_ad"].values == 1
        dates = pd.to_datetime(self.df["publish_date"], errors="coerce").values
        N = len(self.df)
        N_AD = ad_mask.sum()
        reel_mask = is_reel == 1
        feed_mask = is_reel == 0

        # 샘플 기준 상위 200개
        qualified = [r for r in self.results if r.get("recall", 0) >= 0.94]
        top200 = sorted(qualified, key=lambda x: x["drop_rate"], reverse=True)[:200]

        verified = []
        for r in top200:
            try:
                cond = r["condition"]
                # 릴스 파라미터 추출
                reel_part = cond.split(" / ")[0]  # "릴스:V>=1000|L>=5|C>=3"
                v1 = int(reel_part.split("V>=")[1].split("|")[0].replace(",", ""))
                l1 = int(reel_part.split("L>=")[1].split("|")[0])
                c1 = int(reel_part.split("C>=")[1])

                # 피드 파라미터 추출
                feed_part = cond.split(" / ")[1]  # "피드:(F>=3000&D>=2024-01-01)|L>=50|V>=5000"
                f1 = int(feed_part.split("F>=")[1].split("&")[0].replace(",", ""))
                dc = feed_part.split("D>=")[1].split(")")[0]
                l2 = int(feed_part.split("|L>=")[1].split("|")[0])
                v2 = int(feed_part.split("|V>=")[1].replace(",", ""))

                # 전체 데이터로 계산
                reel_keep = reel_mask & ((views >= v1) | (likes >= l1) | (comments >= c1))
                date_mask = dates >= np.datetime64(dc)
                feed_keep = feed_mask & (((followers >= f1) & date_mask) | (likes >= l2) | (views >= v2))
                keep = reel_keep | feed_keep

                ad_kept = keep[ad_mask].sum()
                recall = float(ad_kept) / N_AD
                total_kept = keep.sum()
                drop_rate = 1 - float(total_kept) / N

                verified.append({
                    **r,
                    "recall": round(recall, 4),
                    "drop_rate": round(drop_rate, 4),
                    "ad_kept": int(ad_kept),
                    "total_kept": int(total_kept),
                    "verified": True,
                })
            except Exception as e:
                verified.append({**r, "verified": False, "error": str(e)})

        # 검증 결과로 교체
        self.results = verified
        await self._send_status("verified", 98,
            f"전체 데이터 검증 완료! {len([v for v in verified if v.get('verified')])}개 확정")

    # ─── 최종 랭킹 ───
    async def finalize(self):
        await self._send_status("finalizing", 99, "최종 랭킹 집계 중...")

        qualified = [r for r in self.results if r.get("recall", 0) >= 0.95 and r.get("verified", False)]
        ranked = sorted(qualified, key=lambda x: x["drop_rate"], reverse=True)
        top20 = ranked[:20]

        await self._send("final_ranking", {"rankings": top20})
        await self._send_status("done", 100,
            f"분석 완료! {len(qualified)}개 적격 (전부 SQL 실행 가능, 전체 데이터 검증 완료)")

        # 저장
        import datetime
        save_data = {
            "saved_at": datetime.datetime.now().isoformat(),
            "status": "done",
            "top20": top20,
            "all_results": self.results,
            "log_history": self._log_history,
        }
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, default=str, indent=2)

        return top20

    # ─── 전체 파이프라인 ───
    async def run_full_analysis(self):
        try:
            await self.load_data()
            await self.search()
            await self.verify()
            return await self.finalize()
        except Exception as e:
            await self._send("error", {"message": str(e)})
            raise
