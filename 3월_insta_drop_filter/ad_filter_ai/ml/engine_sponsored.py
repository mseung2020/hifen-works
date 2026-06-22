"""
is_sponsored/is_ppl 기반 + 공격적 필터링 엔진
  - is_sponsored_or_ppl=1 → 무조건 보존 (광고 99.98% 커버)
  - 나머지 OR 조건을 공격적으로 탐색
  - 샘플 10%로 탐색 → 상위 200개 전체 검증
"""

import pandas as pd
import numpy as np
import time, os, json
from typing import Optional, Callable

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(BASE_DIR)
TOTAL_PATH = os.path.join(PARENT_DIR, "total_insta_id_slim.csv")
AD_PATH = os.path.join(PARENT_DIR, "ad_insta_id.csv")
SAVE_PATH = os.path.join(BASE_DIR, "analysis_result.json")


def build_verification_sql(where_clause, label=""):
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
        f"        SELECT DISTINCT post_id FROM hifen.instagram_ppl_brand\n"
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


class SponsoredEngine:

    def __init__(self):
        self.df = None
        self.results = []
        self.status = "idle"
        self.progress = 0
        self._broadcast: Optional[Callable] = None
        self._log_history = []

    def set_broadcast(self, fn):
        self._broadcast = fn

    async def _send(self, msg_type, data):
        payload = {"type": msg_type, **data}
        self._log_history.append(payload)
        if self._broadcast:
            await self._broadcast(json.dumps(payload, ensure_ascii=False, default=str))

    async def _send_status(self, status, progress, detail=""):
        self.status = status
        self.progress = progress
        await self._send("status", {"status": status, "progress": progress, "detail": detail})

    async def load_data(self):
        await self._send_status("loading", 0, "데이터 로드 시작...")
        t0 = time.time()

        self.df = pd.read_csv(TOTAL_PATH, sep=";",
            usecols=["post_id","is_reel","views","likes","comments","followers",
                      "publish_date","is_sponsored","is_ppl"],
            dtype={"post_id":"str","is_reel":"int8","views":"int32","likes":"int32",
                   "comments":"int32","followers":"int32","publish_date":"str",
                   "is_sponsored":"int8","is_ppl":"int8"})

        ad = pd.read_csv(AD_PATH, sep=";", quotechar='"',
                         usecols=["post_id"], dtype={"post_id":"str"})
        self.df["is_ad"] = self.df["post_id"].isin(set(ad["post_id"])).astype("int8")
        del ad

        n = len(self.df)
        n_ad = (self.df["is_ad"] == 1).sum()
        n_sp = ((self.df["is_sponsored"] == 1) | (self.df["is_ppl"] == 1)).sum()

        await self._send_status("loaded", 30,
            f"로드 완료: {n:,}건 / 광고 {n_ad:,}건 / is_sponsored_or_ppl=1: {n_sp:,}건 ({time.time()-t0:.1f}s)")
        await self._send("data_summary", {
            "total": n, "ad": int(n_ad), "normal": int(n - n_ad),
            "reel": int((self.df["is_reel"]==1).sum()),
            "post": int((self.df["is_reel"]==0).sum()),
        })

    async def search(self):
        await self._send_status("simulating", 35, "샘플 생성 + 사전 계산...")

        # 전체 배열
        full_views = self.df["views"].values
        full_likes = self.df["likes"].values
        full_comments = self.df["comments"].values
        full_followers = self.df["followers"].values
        full_dates = pd.to_datetime(self.df["publish_date"], errors="coerce").values
        full_ad_mask = self.df["is_ad"].values == 1
        full_sp = (self.df["is_sponsored"].values == 1) | (self.df["is_ppl"].values == 1)
        N = len(self.df)
        N_AD = full_ad_mask.sum()

        # 10% 샘플
        ad_idx = np.where(full_ad_mask)[0]
        normal_idx = np.where(~full_ad_mask)[0]
        np.random.seed(42)
        sample_normal = np.random.choice(normal_idx, size=len(normal_idx)//10, replace=False)
        sidx = np.sort(np.concatenate([ad_idx, sample_normal]))

        views = full_views[sidx]
        likes = full_likes[sidx]
        comments = full_comments[sidx]
        followers = full_followers[sidx]
        dates = full_dates[sidx]
        ad_mask = self.df["is_ad"].values[sidx] == 1
        sp_mask = full_sp[sidx]
        S_N = len(sidx)
        S_N_AD = ad_mask.sum()

        # is_sponsored_or_ppl=1인 게시물의 광고 커버리지
        sp_ad_kept = (sp_mask & ad_mask).sum()
        sp_recall = sp_ad_kept / S_N_AD
        sp_total_kept = sp_mask.sum()
        await self._send_status("simulating", 40,
            f"is_sponsored_or_ppl=1만으로: recall {sp_recall*100:.2f}% / 보존 {sp_total_kept:,}건 ({sp_total_kept/S_N*100:.1f}%)")

        # 나머지 recall 필요량 = 95% - sp_recall
        remaining_recall_needed = 0.95 - sp_recall
        remaining_ad = S_N_AD - sp_ad_kept  # sp로 커버 안 되는 광고 수
        await self._send_status("simulating", 42,
            f"추가로 필요한 광고: {remaining_ad}건 (sp 미커버 {remaining_recall_needed*100:.2f}%)")

        # 후보값 정의 — 공격적으로!
        ad_v = views[ad_mask]
        ad_l = likes[ad_mask]
        ad_f = followers[ad_mask]

        # 기존보다 훨씬 높은 값까지
        v_vals = sorted(set(
            [0] + list(range(0, 50001, 2000))
            + [int(np.percentile(ad_v, p)) for p in [5,10,25,50,75]]
        ))
        l_vals = sorted(set(
            [0, 1, 3, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
        ))
        c_vals = sorted(set(
            [0, 1, 3, 5, 10, 20, 50, 100]
        ))
        f_vals = sorted(set(
            [0] + list(range(0, 50001, 2500))
            + [int(np.percentile(ad_f, p)) for p in [5,10,25,50,75]]
        ))
        date_cuts = ["2025-07-01", "2025-01-01", "2024-07-01", "2024-01-01",
                     "2023-01-01", "2022-01-01"]

        await self._send_status("simulating", 45,
            f"후보: V={len(v_vals)} L={len(l_vals)} C={len(c_vals)} F={len(f_vals)} D={len(date_cuts)}")

        # 사전 캐싱
        sp_keep = sp_mask  # is_sponsored_or_ppl=1 기본 보존
        v_masks = {v: views >= v for v in v_vals}
        l_masks = {l: likes >= l for l in l_vals}
        c_masks = {c: comments >= c for c in c_vals}
        f_masks = {f: followers >= f for f in f_vals}
        d_masks = {dc: dates >= np.datetime64(dc) for dc in date_cuts}

        combo_results = []
        best_drop = 0
        total_tried = 0
        total_found = 0

        async def _emit(result):
            nonlocal best_drop, total_found
            total_found += 1
            combo_results.append(result)
            if result["drop_rate"] < 0.30:
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
            qualified = [r for r in combo_results if r.get("drop_rate", 0) >= 0.30]
            ranked = sorted(qualified, key=lambda x: x["drop_rate"], reverse=True)
            save_data = {
                "saved_at": datetime.datetime.now().isoformat(),
                "status": "in_progress",
                "total_tried": total_tried,
                "total_found": total_found,
                "top20": ranked[:20],
                "all_results": [r for r in combo_results if r.get("drop_rate", 0) >= 0.30],
                "log_history": self._log_history,
            }
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, default=str)

        t_start = time.time()

        # ══════════════════════════════════════
        # 패턴 1: sp=1 OR V>=v OR L>=l OR F>=f
        # ══════════════════════════════════════
        await self._send_status("simulating", 50, "패턴1: sp=1 OR V OR L OR F...")
        for v in v_vals:
            for l in l_vals:
                for f in f_vals:
                    total_tried += 1
                    keep = sp_keep | v_masks[v] | l_masks[l] | f_masks[f]
                    ad_kept = keep[ad_mask].sum()
                    recall = ad_kept / S_N_AD
                    if recall < 0.95:
                        continue
                    drop = 1 - keep.sum() / S_N

                    where = (f"(a.is_sponsored = 1 OR a.is_ppl = 1)\n"
                             f"        OR a.views >= {v}\n"
                             f"        OR a.likes >= {l}\n"
                             f"        OR b.followers >= {f}")
                    await _emit({
                        "method": "sp+OR",
                        "condition": f"sp=1 OR V>={v:,} OR L>={l:,} OR F>={f:,}",
                        "recall": round(float(recall), 4),
                        "drop_rate": round(float(drop), 4),
                        "ad_kept": int(ad_kept), "total_kept": int(keep.sum()),
                        "sql": build_verification_sql(where, "sp+OR"),
                    })

                if total_tried % 50000 < len(f_vals):
                    elapsed = time.time() - t_start
                    await self._send_status("simulating", 55,
                        f"[패턴1] {total_tried:,}개 / {total_found:,}유효 (최고 {best_drop*100:.1f}%) [{total_tried/max(elapsed,1):,.0f}건/초]")
                    _save_now()

        await self._send_status("simulating", 65, f"패턴1 완료 ({total_found:,}개, 최고 {best_drop*100:.1f}%)")
        _save_now()

        # ══════════════════════════════════════
        # 패턴 2: sp=1 OR (F>=f AND D>=d) OR L>=l OR V>=v
        # ══════════════════════════════════════
        await self._send_status("simulating", 65, "패턴2: sp=1 OR (F&D) OR L OR V...")
        for v in v_vals:
            for l in l_vals:
                for f in f_vals:
                    for dc in date_cuts:
                        total_tried += 1
                        keep = sp_keep | (f_masks[f] & d_masks[dc]) | l_masks[l] | v_masks[v]
                        ad_kept = keep[ad_mask].sum()
                        recall = ad_kept / S_N_AD
                        if recall < 0.95:
                            continue
                        drop = 1 - keep.sum() / S_N

                        where = (f"(a.is_sponsored = 1 OR a.is_ppl = 1)\n"
                                 f"        OR (b.followers >= {f} AND a.publish_date >= '{dc}')\n"
                                 f"        OR a.likes >= {l}\n"
                                 f"        OR a.views >= {v}")
                        await _emit({
                            "method": "sp+F&D",
                            "condition": f"sp=1 OR (F>={f:,}&D>={dc}) OR L>={l:,} OR V>={v:,}",
                            "recall": round(float(recall), 4),
                            "drop_rate": round(float(drop), 4),
                            "ad_kept": int(ad_kept), "total_kept": int(keep.sum()),
                            "sql": build_verification_sql(where, "sp+F&D"),
                        })

                    if total_tried % 50000 < len(date_cuts) * 2:
                        elapsed = time.time() - t_start
                        await self._send_status("simulating", 75,
                            f"[패턴2] {total_tried:,}개 / {total_found:,}유효 (최고 {best_drop*100:.1f}%) [{total_tried/max(elapsed,1):,.0f}건/초]")
                        _save_now()

        await self._send_status("simulating", 85, f"패턴2 완료 ({total_found:,}개, 최고 {best_drop*100:.1f}%)")
        _save_now()

        # ══════════════════════════════════════
        # 패턴 3: sp=1 OR V>=v OR L>=l OR C>=c OR F>=f
        # ══════════════════════════════════════
        await self._send_status("simulating", 85, "패턴3: sp=1 OR V OR L OR C OR F...")
        for v in v_vals:
            for l in l_vals:
                for c in c_vals:
                    for f in f_vals:
                        total_tried += 1
                        keep = sp_keep | v_masks[v] | l_masks[l] | c_masks[c] | f_masks[f]
                        ad_kept = keep[ad_mask].sum()
                        recall = ad_kept / S_N_AD
                        if recall < 0.95:
                            continue
                        drop = 1 - keep.sum() / S_N

                        where = (f"(a.is_sponsored = 1 OR a.is_ppl = 1)\n"
                                 f"        OR a.views >= {v}\n"
                                 f"        OR a.likes >= {l}\n"
                                 f"        OR a.comments >= {c}\n"
                                 f"        OR b.followers >= {f}")
                        await _emit({
                            "method": "sp+VLCF",
                            "condition": f"sp=1 OR V>={v:,} OR L>={l:,} OR C>={c} OR F>={f:,}",
                            "recall": round(float(recall), 4),
                            "drop_rate": round(float(drop), 4),
                            "ad_kept": int(ad_kept), "total_kept": int(keep.sum()),
                            "sql": build_verification_sql(where, "sp+VLCF"),
                        })

                    if total_tried % 50000 < len(f_vals) * 2:
                        elapsed = time.time() - t_start
                        await self._send_status("simulating", 92,
                            f"[패턴3] {total_tried:,}개 / {total_found:,}유효 (최고 {best_drop*100:.1f}%) [{total_tried/max(elapsed,1):,.0f}건/초]")
                        _save_now()

        _save_now()
        self.results = combo_results
        elapsed = time.time() - t_start
        await self._send_status("simulated", 95,
            f"탐색 완료! {total_tried:,}개 → {total_found:,}유효 (최고 {best_drop*100:.1f}%, {elapsed:.0f}초)")

    async def verify(self):
        await self._send_status("verifying", 96, "상위 200개 전체 데이터 검증 중...")

        views = self.df["views"].values
        likes = self.df["likes"].values
        comments = self.df["comments"].values
        followers = self.df["followers"].values
        dates = pd.to_datetime(self.df["publish_date"], errors="coerce").values
        ad_mask = self.df["is_ad"].values == 1
        sp = (self.df["is_sponsored"].values == 1) | (self.df["is_ppl"].values == 1)
        N = len(self.df)
        N_AD = ad_mask.sum()

        qualified = [r for r in self.results if r.get("drop_rate", 0) >= 0.30]
        top200 = sorted(qualified, key=lambda x: x["drop_rate"], reverse=True)[:200]

        verified = []
        for r in top200:
            try:
                cond = r["condition"]
                method = r["method"]

                if "sp+OR" == method:
                    parts = cond.replace("sp=1 OR ", "").split(" OR ")
                    v = int(parts[0].split("V>=")[1].replace(",",""))
                    l = int(parts[1].split("L>=")[1].replace(",",""))
                    f = int(parts[2].split("F>=")[1].replace(",",""))
                    keep = sp | (views >= v) | (likes >= l) | (followers >= f)

                elif "sp+F&D" == method:
                    v = int(cond.split("V>=")[1].replace(",",""))
                    l = int(cond.split("L>=")[1].split(" OR")[0].replace(",",""))
                    fd = cond.split("(F>=")[1].split(")")[0]
                    f = int(fd.split("&D>=")[0].replace(",",""))
                    dc = fd.split("&D>=")[1]
                    keep = sp | ((followers >= f) & (dates >= np.datetime64(dc))) | (likes >= l) | (views >= v)

                elif "sp+VLCF" == method:
                    parts = cond.replace("sp=1 OR ", "").split(" OR ")
                    v = int(parts[0].split("V>=")[1].replace(",",""))
                    l = int(parts[1].split("L>=")[1].replace(",",""))
                    c = int(parts[2].split("C>=")[1])
                    f = int(parts[3].split("F>=")[1].replace(",",""))
                    keep = sp | (views >= v) | (likes >= l) | (comments >= c) | (followers >= f)

                else:
                    continue

                ad_kept = keep[ad_mask].sum()
                recall = float(ad_kept) / N_AD
                drop = 1 - float(keep.sum()) / N

                verified.append({
                    **r,
                    "recall": round(recall, 4),
                    "drop_rate": round(drop, 4),
                    "ad_kept": int(ad_kept),
                    "total_kept": int(keep.sum()),
                    "verified": True,
                })
            except Exception as e:
                verified.append({**r, "verified": False, "error": str(e)})

        self.results = verified
        await self._send_status("verified", 98,
            f"검증 완료! {len([v for v in verified if v.get('verified')])}개 확정")

    async def finalize(self):
        await self._send_status("finalizing", 99, "최종 랭킹...")

        qualified = [r for r in self.results if r.get("recall", 0) >= 0.95 and r.get("verified", False)]
        ranked = sorted(qualified, key=lambda x: x["drop_rate"], reverse=True)
        top20 = ranked[:20]

        await self._send("final_ranking", {"rankings": top20})
        await self._send_status("done", 100,
            f"완료! {len(qualified)}개 적격 (전부 SQL 실행 가능, 전체 데이터 검증)")

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

    async def run_full_analysis(self):
        try:
            await self.load_data()
            await self.search()
            await self.verify()
            return await self.finalize()
        except Exception as e:
            await self._send("error", {"message": str(e)})
            raise
