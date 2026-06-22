"""
ML 엔진 — XGBoost(힌트용) + SQL 실행 가능한 조건 탐색
  - XGBoost/DecisionTree: 어떤 변수가 중요한지 힌트만 제공
  - 최종 랭킹: SQL WHERE절로 직접 변환 가능한 조건만 포함
  - SQL 출력: WITH stats 검증 쿼리 양식 (워크벤치에서 바로 실행 가능)
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import time, os, json, asyncio
from typing import Optional, Callable

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(BASE_DIR)
TOTAL_PATH = os.path.join(PARENT_DIR, "total_insta_id_slim.csv")
AD_PATH = os.path.join(PARENT_DIR, "ad_insta_id.csv")
SAVE_PATH = os.path.join(BASE_DIR, "analysis_result.json")


def build_verification_sql(where_clause: str, label: str = "") -> str:
    """WHERE 조건을 받아서 워크벤치용 WITH stats 검증 쿼리를 생성"""
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


class AdFilterEngine:
    """광고 필터링 최적화 엔진"""

    def __init__(self):
        self.df = None
        self.model = None
        self.results = []
        self.status = "idle"
        self.progress = 0
        self._broadcast: Optional[Callable] = None
        self._log_history = []
        self.last_saved = None

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
                   "views": "int32", "likes": "int32", "comments": "int32", "followers": "int32",
                   "publish_date": "str"},
        )
        await self._send_status("loading", 30, f"total 로드 완료: {len(self.df):,}건")

        ad = pd.read_csv(AD_PATH, sep=";", quotechar='"',
                         usecols=["post_id"], dtype={"post_id": "str"})
        self.df["is_ad"] = self.df["post_id"].isin(set(ad["post_id"])).astype("int8")
        del ad

        n_total = len(self.df)
        n_ad = (self.df["is_ad"] == 1).sum()

        await self._send_status("loaded", 40,
                                f"데이터 준비 완료: 전체 {n_total:,}건 / 광고 {n_ad:,}건 ({time.time()-t0:.1f}s)")

        await self._send("data_summary", {
            "total": n_total,
            "ad": int(n_ad),
            "normal": int(n_total - n_ad),
            "reel": int((self.df["is_reel"] == 1).sum()),
            "post": int((self.df["is_reel"] == 0).sum()),
        })

    # ─── XGBoost 학습 (힌트용) ───
    async def train_xgboost(self):
        await self._send_status("training", 45, "XGBoost 학습 (피처 중요도 분석용)...")

        features = ["views", "likes", "comments", "followers"]
        X = self.df[features].values
        y = self.df["is_ad"].values

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )

        scale = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

        model = xgb.XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            scale_pos_weight=scale, eval_metric="aucpr",
            tree_method="hist", random_state=42, n_jobs=-1,
        )

        t0 = time.time()
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        self.model = model

        await self._send_status("trained", 55, f"XGBoost 학습 완료 ({time.time()-t0:.1f}s)")

        importance = dict(zip(features, model.feature_importances_.tolist()))
        await self._send("feature_importance", {"importance": importance})

        y_pred = model.predict(X_val)
        report = classification_report(y_val, y_pred, output_dict=True)
        await self._send("validation", {
            "accuracy": report["accuracy"],
            "ad_precision": report["1"]["precision"],
            "ad_recall": report["1"]["recall"],
            "ad_f1": report["1"]["f1-score"],
        })

    # ─── Decision Tree 규칙 (참고용) ───
    async def extract_tree_rules(self):
        await self._send_status("tree_rules", 60, "Decision Tree 규칙 추출 (참고용)...")

        from sklearn.tree import DecisionTreeClassifier, export_text

        features = ["views", "likes", "comments", "followers"]
        X = self.df[features].values
        y = self.df["is_ad"].values
        ad_mask = y == 1
        N = len(self.df)
        N_AD = ad_mask.sum()

        for depth in [3, 4, 5, 6]:
            tree = DecisionTreeClassifier(
                max_depth=depth, class_weight="balanced", random_state=42,
            )
            tree.fit(X, y)
            y_pred = tree.predict(X)

            keep = y_pred == 1
            ad_kept = keep[ad_mask].sum()
            recall = ad_kept / N_AD
            drop_rate = 1 - keep.sum() / N

            tree_text = export_text(tree, feature_names=features, max_depth=depth)

            await self._send("rule_found", {
                "method": f"DecisionTree (depth={depth})",
                "recall": round(float(recall) * 100, 2),
                "drop_rate": round(float(drop_rate) * 100, 2),
                "tree_text": tree_text[:1000],
            })

        await self._send_status("tree_done", 68, "Decision Tree 규칙 추출 완료 (참고용)")

    # ─── SQL 실행 가능한 조건 시뮬레이션 ───
    async def simulate_combinations(self):
        await self._send_status("simulating", 70, "SQL 변환 가능한 조건 시뮬레이션 시작...")

        views = self.df["views"].values
        likes = self.df["likes"].values
        comments = self.df["comments"].values
        followers = self.df["followers"].values
        is_reel = self.df["is_reel"].values
        ad_mask = self.df["is_ad"].values == 1
        N = len(self.df)
        N_AD = ad_mask.sum()

        ad_v = views[ad_mask]
        ad_l = likes[ad_mask]
        ad_c = comments[ad_mask]
        ad_f = followers[ad_mask]

        # 탐색 후보: percentile 촘촘하게 + 구간 보간 (기존 판다스 수준 복원)
        v_vals = sorted(set(
            [0] + [int(np.percentile(ad_v, p)) for p in [1,2,3,5,7,10,15,25]]
            + list(range(0, 10001, 500))
        ))
        l_vals = sorted(set(
            [0] + [int(np.percentile(ad_l, p)) for p in [1,2,3,5,7,10,15,25]]
            + list(range(0, 1001, 50))
        ))
        c_vals = sorted(set(
            [0] + [int(np.percentile(ad_c, p)) for p in [1,2,3,5,7,10,15,25]]
            + list(range(0, 201, 10))
        ))
        f_vals = sorted(set(
            [0] + [int(np.percentile(ad_f, p)) for p in [1,2,3,5,7,10,15,25]]
            + list(range(0, 50001, 2500))
        ))

        await self._send_status("simulating", 72,
            f"탐색 후보: V={len(v_vals)}개 × L={len(l_vals)}개 × C={len(c_vals)}개 × F={len(f_vals)}개")

        combo_results = []
        best_drop = 0
        total_tried = 0
        total_found = 0
        current_pattern = ""  # 현재 진행 중인 패턴 추적

        # ── 이전 중간 저장 복원 ──
        prev = self.load_previous()
        skip_patterns = set()
        or_resume_v = 0  # OR 패턴 재개 시작 V값
        if prev and prev.get("status") == "in_progress":
            combo_results = prev.get("all_results", [])
            total_found = len(combo_results)
            skip_patterns = set(prev.get("completed_patterns", []))
            or_resume_v = prev.get("or_resume_from_v", 0)
            if combo_results:
                best_drop = max(r.get("drop_rate", 0) for r in combo_results)
            await self._send_status("simulating", 72,
                f"이전 결과 복원: {total_found:,}개 로드, 최고 삭제율 {best_drop*100:.1f}% (완료 패턴: {skip_patterns})")
            # 복원된 상위 결과를 프론트에 재전송
            ranked = sorted([r for r in combo_results if r.get("drop_rate", 0) >= 0.20],
                            key=lambda x: x["drop_rate"], reverse=True)
            for r in ranked[:20]:
                await self._send("combo_result", {
                    **r,
                    "recall_pct": round(r["recall"] * 100, 2),
                    "drop_pct": round(r["drop_rate"] * 100, 2),
                })

        async def _emit(result):
            """유효 조합 발견 시 삭제율 20% 이상만 프론트로 전송"""
            nonlocal best_drop, total_found
            total_found += 1
            combo_results.append(result)

            if result["drop_rate"] < 0.20:
                return

            # 최고 삭제율 갱신 시 → 전송
            if result["drop_rate"] > best_drop:
                best_drop = result["drop_rate"]
                await self._send("combo_result", {
                    **result,
                    "recall_pct": round(result["recall"] * 100, 2),
                    "drop_pct": round(result["drop_rate"] * 100, 2),
                })

            # 랭킹 갱신 또는 500개마다 중간 저장 (서버 죽어도 복구)
            if result["drop_rate"] > best_drop or total_found % 500 == 0:
                _save_now()

        def _save_now():
            """즉시 중간 저장"""
            import datetime
            qualified = [r for r in combo_results if r.get("drop_rate", 0) >= 0.20]
            ranked = sorted(qualified, key=lambda x: x["drop_rate"], reverse=True)
            save_data = {
                "saved_at": datetime.datetime.now().isoformat(),
                "status": "in_progress",
                "completed_patterns": list(skip_patterns),
                "current_pattern": current_pattern,
                "total_tried": total_tried,
                "total_found": total_found,
                "top20": ranked[:20],
                "all_results": combo_results,
                "log_history": self._log_history,
            }
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, default=str)

        async def _progress(pattern_name, pct):
            """주기적 진행률 갱신"""
            nonlocal total_tried
            total_tried += 1
            if total_tried % 5000 == 0:
                await self._send_status("simulating", pct,
                    f"[{pattern_name}] {total_tried:,}개 탐색 / {total_found:,}개 유효 (최고 삭제율 {best_drop*100:.1f}%)")

        # ── 패턴 1: OR 조건 ──
        current_pattern = "OR"
        if "OR" in skip_patterns:
            await self._send_status("simulating", 80, "패턴1: OR 조건 — 이전 완료, 건너뜀")
        else:
            if or_resume_v > 0:
                await self._send_status("simulating", 72, f"패턴1: OR 조건 V>={or_resume_v}부터 재개...")
            else:
                await self._send_status("simulating", 72, f"패턴1: OR 조건 탐색 시작...")
            for v in v_vals:
                if v < or_resume_v:
                    continue  # 이전에 완료한 부분 건너뜀
                v_pass = views >= v
                for l in l_vals:
                    l_pass = likes >= l
                    for c in c_vals:
                        c_pass = comments >= c
                        for f in f_vals:
                            await _progress("OR", 75)
                            keep = v_pass | l_pass | c_pass | (followers >= f)
                            ad_kept = keep[ad_mask].sum()
                            recall = ad_kept / N_AD
                            if recall < 0.95:
                                continue
                            drop = 1 - keep.sum() / N

                            where = (f"a.views >= {v} OR a.likes >= {l} "
                                     f"OR a.comments >= {c} OR b.followers >= {f}")

                            await _emit({
                                "method": "OR 조건",
                                "condition": f"V>={v:,} OR L>={l:,} OR C>={c} OR F>={f:,}",
                                "recall": round(float(recall), 4),
                                "drop_rate": round(float(drop), 4),
                                "ad_kept": int(ad_kept),
                                "total_kept": int(keep.sum()),
                                "sql": build_verification_sql(where, f"OR 조건: V>={v} L>={l} C>={c} F>={f}"),
                            })
            skip_patterns.add("OR")
            _save_now()

        await self._send_status("simulating", 80, f"OR 조건 완료 ({total_found:,}개 유효, 최고 삭제율 {best_drop*100:.1f}%)")

        # ── 패턴 2: is_reel 분리 + AND/OR 혼합 ──
        reel_mask = is_reel == 1
        post_mask = is_reel == 0

        # AND/OR은 4중 루프이므로 주요 후보로 축소 (그래도 ~10^4 = 10,000 조합)
        v_vals2 = sorted(set(
            [int(np.percentile(ad_v, p)) for p in [1,3,5,10,25]]
            + list(range(0, 10001, 1000))
        ))
        l_vals2 = sorted(set(
            [int(np.percentile(ad_l, p)) for p in [1,3,5,10,25]]
            + list(range(0, 1001, 100))
        ))
        c_vals2 = sorted(set(
            [int(np.percentile(ad_c, p)) for p in [1,3,5,10,25]]
            + list(range(0, 201, 20))
        ))
        f_vals2 = sorted(set(
            [int(np.percentile(ad_f, p)) for p in [1,3,5,10,25]]
            + list(range(0, 50001, 5000))
        ))

        current_pattern = "AND/OR"
        if "AND/OR" in skip_patterns:
            await self._send_status("simulating", 88, "패턴2: AND/OR — 이전 완료, 건너뜀")
        else:
            await self._send_status("simulating", 82, f"패턴2: AND/OR 혼합 탐색 시작...")
            for v in v_vals2:
                for l in l_vals2:
                    l_pass = likes >= l
                    for c in c_vals2:
                        for f in f_vals2:
                            await _progress("AND/OR", 85)
                            reel_keep = reel_mask & (((views >= v) & (comments >= c)) | l_pass)
                            post_keep = post_mask & (((followers >= f) & l_pass) | (views >= v))

                            keep = reel_keep | post_keep
                            ad_kept = keep[ad_mask].sum()
                            recall = ad_kept / N_AD
                            if recall < 0.95:
                                continue
                            drop = 1 - keep.sum() / N

                            where = (
                                f"(a.is_reel = 1 AND ((a.views >= {v} AND a.comments >= {c}) OR a.likes >= {l}))\n"
                                f"        OR\n"
                                f"        (a.is_reel = 0 AND ((b.followers >= {f} AND a.likes >= {l}) OR a.views >= {v}))"
                            )

                            await _emit({
                                "method": "분리 AND/OR",
                                "condition": (f"릴스:(V>={v:,} AND C>={c}) OR L>={l:,} | "
                                              f"일반:(F>={f:,} AND L>={l:,}) OR V>={v:,}"),
                                "recall": round(float(recall), 4),
                                "drop_rate": round(float(drop), 4),
                                "ad_kept": int(ad_kept),
                                "total_kept": int(keep.sum()),
                                "sql": build_verification_sql(where, f"분리 AND/OR: V>={v} L>={l} C>={c} F>={f}"),
                            })
            skip_patterns.add("AND/OR")
            _save_now()

        await self._send_status("simulating", 88, f"AND/OR 완료 ({total_found:,}개 유효, 최고 삭제율 {best_drop*100:.1f}%)")

        # ── 패턴 3: engagement + followers ──
        eng = likes + comments * 2
        e_vals = sorted(set(
            [int(np.percentile(eng[ad_mask], p)) for p in [1,3,5,10,25]]
            + list(range(0, 2001, 100))
        ))

        current_pattern = "Engagement"
        if "Engagement" in skip_patterns:
            await self._send_status("simulating", 93, "패턴3: Engagement — 이전 완료, 건너뜀")
        else:
            await self._send_status("simulating", 89, f"패턴3: Engagement+Followers 탐색 시작...")
            for e in e_vals:
                for f in f_vals:
                    f_pass = followers >= f
                    for v in v_vals:
                        await _progress("Engagement", 91)
                        keep = ((eng >= e) & f_pass) | (views >= v)
                        ad_kept = keep[ad_mask].sum()
                        recall = ad_kept / N_AD
                        if recall < 0.95:
                            continue
                        drop = 1 - keep.sum() / N

                        where = (
                            f"((a.likes + a.comments * 2) >= {e} AND b.followers >= {f})\n"
                            f"        OR a.views >= {v}"
                        )

                        await _emit({
                            "method": "Engagement+Followers",
                            "condition": f"(L+C*2>={e:,} AND F>={f:,}) OR V>={v:,}",
                            "recall": round(float(recall), 4),
                            "drop_rate": round(float(drop), 4),
                            "ad_kept": int(ad_kept),
                            "total_kept": int(keep.sum()),
                            "sql": build_verification_sql(where, f"Engagement: E>={e} F>={f} V>={v}"),
                        })
            skip_patterns.add("Engagement")
            _save_now()

        await self._send_status("simulating", 93, f"Engagement 완료 ({total_found:,}개 유효, 최고 삭제율 {best_drop*100:.1f}%)")

        # ── 패턴 4: followers 구간별 다른 likes 기준 ──
        current_pattern = "Followers구간"
        if "Followers구간" in skip_patterns:
            await self._send_status("simulating", 97, "패턴4: Followers구간별 — 이전 완료, 건너뜀")
        else:
            await self._send_status("simulating", 94, f"패턴4: Followers 구간별 탐색 시작...")
            for f_high in f_vals2:
                for f_low in [x for x in f_vals2 if x < f_high]:
                    for l_high in l_vals2:
                        for l_low in [x for x in l_vals2 if x > l_high]:
                            for v in v_vals2:
                                await _progress("Followers구간", 96)
                                keep = (
                                    ((followers >= f_high) & (likes >= l_high))
                                    | ((followers >= f_low) & (likes >= l_low))
                                    | (views >= v)
                                )
                                ad_kept = keep[ad_mask].sum()
                                recall = ad_kept / N_AD
                                if recall < 0.95:
                                    continue
                                drop = 1 - keep.sum() / N

                                where = (
                                    f"(b.followers >= {f_high} AND a.likes >= {l_high})\n"
                                    f"        OR (b.followers >= {f_low} AND a.likes >= {l_low})\n"
                                    f"        OR a.views >= {v}"
                                )

                                await _emit({
                                    "method": "Followers 구간별",
                                    "condition": f"(F>={f_high:,} AND L>={l_high:,}) OR (F>={f_low:,} AND L>={l_low:,}) OR V>={v:,}",
                                    "recall": round(float(recall), 4),
                                    "drop_rate": round(float(drop), 4),
                                    "ad_kept": int(ad_kept),
                                    "total_kept": int(keep.sum()),
                                    "sql": build_verification_sql(where, f"Followers 구간별"),
                                })
            skip_patterns.add("Followers구간")
            _save_now()

        await self._send_status("simulating", 97,
            f"기존 패턴 완료 ({total_found:,}개). 신규 패턴 A~D 시작...")

        # ══════════════════════════════════════════════
        # 신규 패턴 A: LOG 복합 점수 (SQL 직접 실행 가능)
        # ══════════════════════════════════════════════
        current_pattern = "LOG점수"
        if "LOG점수" in skip_patterns:
            await self._send_status("simulating", 97, "패턴A: LOG점수 — 이전 완료, 건너뜀")
        else:
            await self._send_status("simulating", 97, "패턴A: LOG 복합 점수 탐색 시작...")

            # is_reel별 다른 가중치 세트
            log_weight_sets = [
                ("균형",       (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0)),
                ("likes강화",  (0.3, 2.0, 0.5, 1.5), (0.3, 2.0, 0.5, 1.5)),
                ("유형특화",   (0.2, 1.5, 0.5, 1.5), (1.5, 0.5, 0.5, 0.8)),
                ("fol강화",    (0.3, 1.0, 0.3, 2.0), (1.0, 0.5, 0.3, 1.5)),
                ("engage",     (0.5, 1.5, 1.0, 1.0), (1.0, 1.0, 0.5, 0.8)),
            ]

            for w_label, post_w, reel_w in log_weight_sets:
                scores = np.zeros(N, dtype=np.float32)
                p_idx = np.where(post_mask)[0]
                r_idx = np.where(reel_mask)[0]

                scores[p_idx] = (
                    post_w[0] * np.log1p(np.maximum(views[p_idx], 0).astype(np.float32))
                    + post_w[1] * np.log1p(np.maximum(likes[p_idx], 0).astype(np.float32))
                    + post_w[2] * np.log1p(np.maximum(comments[p_idx], 0).astype(np.float32))
                    + post_w[3] * np.log1p(np.maximum(followers[p_idx], 0).astype(np.float32))
                )
                scores[r_idx] = (
                    reel_w[0] * np.log1p(np.maximum(views[r_idx], 0).astype(np.float32))
                    + reel_w[1] * np.log1p(np.maximum(likes[r_idx], 0).astype(np.float32))
                    + reel_w[2] * np.log1p(np.maximum(comments[r_idx], 0).astype(np.float32))
                    + reel_w[3] * np.log1p(np.maximum(followers[r_idx], 0).astype(np.float32))
                )

                ad_scores = scores[ad_mask]

                for pct in np.arange(0.5, 10.0, 0.25):
                    await _progress("LOG점수", 97)
                    cutoff = float(np.percentile(ad_scores, pct))
                    keep = scores >= cutoff
                    ad_kept = keep[ad_mask].sum()
                    recall = ad_kept / N_AD
                    if recall < 0.95:
                        continue
                    drop = 1 - keep.sum() / N

                    # is_reel별 다른 가중치이므로 CASE WHEN으로 SQL 표현
                    where = (
                        f"CASE WHEN a.is_reel = 1 THEN\n"
                        f"            ({reel_w[0]}*LOG(1+a.views) + {reel_w[1]}*LOG(1+a.likes) "
                        f"+ {reel_w[2]}*LOG(1+a.comments) + {reel_w[3]}*LOG(1+COALESCE(b.followers,0)))\n"
                        f"        ELSE\n"
                        f"            ({post_w[0]}*LOG(1+a.views) + {post_w[1]}*LOG(1+a.likes) "
                        f"+ {post_w[2]}*LOG(1+a.comments) + {post_w[3]}*LOG(1+COALESCE(b.followers,0)))\n"
                        f"        END >= {cutoff:.4f}"
                    )

                    await _emit({
                        "method": "LOG점수",
                        "condition": f"{w_label}: cutoff>={cutoff:.2f} (p{pct:.1f})",
                        "recall": round(float(recall), 4),
                        "drop_rate": round(float(drop), 4),
                        "ad_kept": int(ad_kept),
                        "total_kept": int(keep.sum()),
                        "sql": build_verification_sql(where, f"LOG점수 ({w_label}, p{pct:.1f})"),
                    })

            skip_patterns.add("LOG점수")
            _save_now()

        # ══════════════════════════════════════════════
        # 신규 패턴 D: Engagement Rate (비율 기반)
        # ══════════════════════════════════════════════
        current_pattern = "EngRate"
        if "EngRate" in skip_patterns:
            await self._send_status("simulating", 97, "패턴D: EngRate — 이전 완료, 건너뜀")
        else:
            await self._send_status("simulating", 97, "패턴D: Engagement Rate 탐색 시작...")

            # likes / max(followers, 1) >= ratio OR views >= V OR followers >= F_floor
            ratio_vals = [round(x, 4) for x in np.arange(0.001, 0.03, 0.001).tolist()]
            v_rescue = sorted(set(list(range(0, 10001, 500)) + [int(np.percentile(ad_v, p)) for p in [3, 5, 10]]))
            f_floor_vals = sorted(set(list(range(0, 20001, 1000)) + [int(np.percentile(ad_f, p)) for p in [3, 5, 10]]))

            fol_safe = np.maximum(followers, 1).astype(np.float32)
            eng_rate = likes.astype(np.float32) / fol_safe

            for ratio in ratio_vals:
                r_pass = eng_rate >= ratio
                for v in v_rescue:
                    v_pass = views >= v
                    for f_fl in f_floor_vals:
                        await _progress("EngRate", 97)
                        keep = r_pass | v_pass | (followers >= f_fl)
                        ad_kept = keep[ad_mask].sum()
                        recall = ad_kept / N_AD
                        if recall < 0.95:
                            continue
                        drop = 1 - keep.sum() / N

                        where = (
                            f"(a.likes / GREATEST(b.followers, 1)) >= {ratio}\n"
                            f"        OR a.views >= {v}\n"
                            f"        OR b.followers >= {f_fl}"
                        )

                        await _emit({
                            "method": "EngRate",
                            "condition": f"L/F>={ratio} OR V>={v:,} OR F>={f_fl:,}",
                            "recall": round(float(recall), 4),
                            "drop_rate": round(float(drop), 4),
                            "ad_kept": int(ad_kept),
                            "total_kept": int(keep.sum()),
                            "sql": build_verification_sql(where, f"EngRate: ratio>={ratio} V>={v} F>={f_fl}"),
                        })

            skip_patterns.add("EngRate")
            _save_now()

        # ══════════════════════════════════════════════
        # 신규 패턴 B: is_reel 분리 + 넓은 탐색
        # ══════════════════════════════════════════════
        current_pattern = "Reel분리"
        if "Reel분리" in skip_patterns:
            await self._send_status("simulating", 98, "패턴B: Reel분리 — 이전 완료, 건너뜀")
        else:
            await self._send_status("simulating", 98, "패턴B: is_reel 분리 확장 탐색 시작...")

            # 릴스: views>=V1 OR likes>=L1 OR comments>=C1
            # 피드: (followers>=F1 AND likes>=L2) OR views>=V2
            rv1 = sorted(set([0] + [int(np.percentile(ad_v[ad_mask & reel_mask], p)) for p in [3,5,10,25]] + list(range(0, 10001, 1000))))
            rl1 = sorted(set([0] + [int(np.percentile(ad_l[ad_mask & reel_mask], p)) for p in [3,5,10,25]] + list(range(0, 501, 100))))
            rc1 = sorted(set([0] + [int(np.percentile(ad_c[ad_mask & reel_mask], p)) for p in [3,5,10,25]] + list(range(0, 101, 20))))
            pf1 = sorted(set([0] + [int(np.percentile(ad_f[ad_mask & post_mask], p)) for p in [3,5,10,25]] + list(range(0, 20001, 2000))))
            pl2 = sorted(set([0] + [int(np.percentile(ad_l[ad_mask & post_mask], p)) for p in [3,5,10,25]] + list(range(0, 201, 50))))

            for v1 in rv1:
                reel_v = views >= v1
                for l1 in rl1:
                    reel_l = likes >= l1
                    for c1 in rc1:
                        reel_keep = reel_mask & (reel_v | reel_l | (comments >= c1))
                        for f1 in pf1:
                            f_pass = followers >= f1
                            for l2 in pl2:
                                await _progress("Reel분리", 98)
                                post_keep = post_mask & (f_pass & (likes >= l2))

                                keep = reel_keep | post_keep
                                ad_kept = keep[ad_mask].sum()
                                recall = ad_kept / N_AD
                                if recall < 0.95:
                                    continue
                                drop = 1 - keep.sum() / N

                                where = (
                                    f"(a.is_reel = 1 AND (a.views >= {v1} OR a.likes >= {l1} OR a.comments >= {c1}))\n"
                                    f"        OR\n"
                                    f"        (a.is_reel = 0 AND b.followers >= {f1} AND a.likes >= {l2})"
                                )

                                await _emit({
                                    "method": "Reel분리",
                                    "condition": f"릴스:V>={v1:,}|L>={l1:,}|C>={c1} / 피드:F>={f1:,}&L>={l2:,}",
                                    "recall": round(float(recall), 4),
                                    "drop_rate": round(float(drop), 4),
                                    "ad_kept": int(ad_kept),
                                    "total_kept": int(keep.sum()),
                                    "sql": build_verification_sql(where, f"Reel분리"),
                                })

            skip_patterns.add("Reel분리")
            _save_now()

        # ══════════════════════════════════════════════
        # 신규 패턴 C: 3단계 Followers 티어
        # ══════════════════════════════════════════════
        current_pattern = "3단계Fol"
        if "3단계Fol" in skip_patterns:
            await self._send_status("simulating", 99, "패턴C: 3단계Fol — 이전 완료, 건너뜀")
        else:
            await self._send_status("simulating", 99, "패턴C: 3단계 Followers 티어 탐색 시작...")

            f_tier3 = sorted(set([int(np.percentile(ad_f, p)) for p in [25, 50, 75]] + list(range(5000, 20001, 2500))))
            f_tier2 = sorted(set([int(np.percentile(ad_f, p)) for p in [5, 10, 25]] + list(range(1000, 10001, 1000))))
            l_tier3 = [0, 1, 3, 5]  # 대형 계정은 likes 기준 낮게
            l_tier2 = sorted(set([int(np.percentile(ad_l, p)) for p in [5, 10, 25]] + list(range(0, 201, 50))))
            l_tier1 = sorted(set([int(np.percentile(ad_l, p)) for p in [10, 25, 50]] + list(range(50, 501, 100))))
            v_rescue2 = sorted(set(list(range(0, 10001, 1000)) + [int(np.percentile(ad_v, p)) for p in [3, 5, 10]]))

            for f3 in f_tier3:
                f3_pass = followers >= f3
                for l3 in l_tier3:
                    t3_keep = f3_pass & (likes >= l3)
                    for f2 in [x for x in f_tier2 if x < f3]:
                        f2_pass = followers >= f2
                        for l2 in l_tier2:
                            t2_keep = f2_pass & (likes >= l2)
                            for l1 in l_tier1:
                                for v in v_rescue2:
                                    await _progress("3단계Fol", 99)
                                    keep = t3_keep | t2_keep | (likes >= l1) | (views >= v)
                                    ad_kept = keep[ad_mask].sum()
                                    recall = ad_kept / N_AD
                                    if recall < 0.95:
                                        continue
                                    drop = 1 - keep.sum() / N

                                    where = (
                                        f"(b.followers >= {f3} AND a.likes >= {l3})\n"
                                        f"        OR (b.followers >= {f2} AND a.likes >= {l2})\n"
                                        f"        OR a.likes >= {l1}\n"
                                        f"        OR a.views >= {v}"
                                    )

                                    await _emit({
                                        "method": "3단계Fol",
                                        "condition": f"(F>={f3:,}&L>={l3}) OR (F>={f2:,}&L>={l2:,}) OR L>={l1:,} OR V>={v:,}",
                                        "recall": round(float(recall), 4),
                                        "drop_rate": round(float(drop), 4),
                                        "ad_kept": int(ad_kept),
                                        "total_kept": int(keep.sum()),
                                        "sql": build_verification_sql(where, f"3단계Fol"),
                                    })

            skip_patterns.add("3단계Fol")
            _save_now()

        self.results = combo_results
        await self._send_status("simulated", 99,
            f"전체 시뮬레이션 완료! {total_tried:,}개 탐색 → {total_found:,}개 유효 (최고 삭제율 {best_drop*100:.1f}%)")

    # ─── 최종 랭킹 ───
    async def finalize(self):
        await self._send_status("finalizing", 98, "최종 랭킹 집계 중...")

        qualified = [r for r in self.results if r["recall"] >= 0.95]
        ranked = sorted(qualified, key=lambda x: x["drop_rate"], reverse=True)

        top20 = ranked[:20]
        await self._send("final_ranking", {"rankings": top20})
        await self._send_status("done", 100,
                                f"분석 완료! {len(self.results)}개 시나리오 중 {len(qualified)}개 적격 (전부 SQL 실행 가능)")

        self._save_results(top20)
        return top20

    # ─── 결과 저장 ───
    def _save_results(self, top20):
        import datetime
        save_data = {
            "saved_at": datetime.datetime.now().isoformat(),
            "top20": top20,
            "all_results": self.results,
            "log_history": self._log_history,
        }
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, default=str, indent=2)
        self.last_saved = save_data["saved_at"]

    # ─── 이전 결과 로드 ───
    def load_previous(self):
        if not os.path.exists(SAVE_PATH):
            return None
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # ─── 날짜 기반 패턴 E/F/G 시뮬레이션 ───
    async def simulate_date_patterns(self):
        await self._send_status("simulating", 50, "날짜 기반 패턴 E/F/G 시뮬레이션 시작...")

        # ── 1단계: 10% 샘플 생성 (광고는 전부 포함) ──
        await self._send_status("simulating", 50, "10% 샘플 생성 중 (광고 전수 + 일반 10%)...")

        full_ad_mask = self.df["is_ad"].values == 1
        ad_idx = np.where(full_ad_mask)[0]
        normal_idx = np.where(~full_ad_mask)[0]
        np.random.seed(42)
        sample_normal_idx = np.random.choice(normal_idx, size=len(normal_idx) // 10, replace=False)
        sample_idx = np.sort(np.concatenate([ad_idx, sample_normal_idx]))

        # 샘플 배열 (탐색용)
        s_views = self.df["views"].values[sample_idx]
        s_likes = self.df["likes"].values[sample_idx]
        s_comments = self.df["comments"].values[sample_idx]
        s_followers = self.df["followers"].values[sample_idx]
        s_is_reel = self.df["is_reel"].values[sample_idx]
        s_ad_mask = self.df["is_ad"].values[sample_idx] == 1
        s_dates = pd.to_datetime(self.df["publish_date"].iloc[sample_idx], errors="coerce").values
        S_N = len(sample_idx)
        S_N_AD = s_ad_mask.sum()

        # 전체 배열 (검증용)
        views = self.df["views"].values
        likes = self.df["likes"].values
        comments = self.df["comments"].values
        followers = self.df["followers"].values
        is_reel = self.df["is_reel"].values
        ad_mask = full_ad_mask
        pd_dates = pd.to_datetime(self.df["publish_date"], errors="coerce")
        dates = pd_dates.values
        N = len(self.df)
        N_AD = ad_mask.sum()

        reel_mask = is_reel == 1
        post_mask = is_reel == 0

        ad_v = views[ad_mask]
        ad_l = likes[ad_mask]
        ad_f = followers[ad_mask]

        await self._send_status("simulating", 52,
            f"샘플: {S_N:,}건 (광고 {S_N_AD:,} + 일반 {S_N-S_N_AD:,}) / 전체: {N:,}건")

        combo_results = []
        best_drop = 0
        total_tried = 0
        total_found = 0

        # 이전 결과 로드
        prev = self.load_previous()
        skip_patterns = set()
        if prev and prev.get("status") == "in_progress":
            combo_results = prev.get("all_results", [])
            total_found = len(combo_results)
            skip_patterns = set(prev.get("completed_patterns", []))
            if combo_results:
                best_drop = max(r.get("drop_rate", 0) for r in combo_results)
            await self._send_status("simulating", 52,
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
            if total_found % 500 == 0:
                _save_now()

        def _save_now():
            import datetime
            qualified = [r for r in combo_results if r.get("drop_rate", 0) >= 0.20]
            ranked = sorted(qualified, key=lambda x: x["drop_rate"], reverse=True)
            save_data = {
                "saved_at": datetime.datetime.now().isoformat(),
                "status": "in_progress",
                "completed_patterns": list(skip_patterns),
                "total_tried": total_tried,
                "total_found": total_found,
                "top20": ranked[:20],
                "all_results": combo_results,
                "log_history": self._log_history,
            }
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, default=str)

        _progress_counter = [0]  # mutable로 nonlocal 대신 사용

        async def _progress_async(pattern_name, pct):
            """5000회마다만 async 호출 — 나머지는 카운터만 증가"""
            nonlocal total_tried
            total_tried = _progress_counter[0]
            await self._send_status("simulating", pct,
                f"[{pattern_name}] {total_tried:,}개 탐색 / {total_found:,}개 유효 (최고 {best_drop*100:.1f}%)")
            _save_now()

        # 날짜 구간 후보 (2026-01-01 스킵 — 최근 3개월은 의미 없음)
        date_cuts = [
            "2025-07-01", "2025-01-01",
            "2024-07-01", "2024-01-01", "2023-07-01",
            "2023-01-01", "2022-01-01",
        ]
        # 샘플용 날짜 마스크
        s_date_masks = {}
        for dc in date_cuts:
            s_date_masks[dc] = s_dates >= np.datetime64(dc)
        # 전체용 날짜 마스크 (검증 단계에서 사용)
        full_date_masks = {}
        for dc in date_cuts:
            full_date_masks[dc] = dates >= np.datetime64(dc)

        f_vals = sorted(set(
            [0] + [int(np.percentile(ad_f, p)) for p in [1,3,5,10,25,50]]
            + list(range(0, 20001, 1000))
        ))
        l_vals = sorted(set(
            [0, 1, 3, 5, 10, 20, 50, 100, 150, 200, 300, 500]
            + [int(np.percentile(ad_l, p)) for p in [1,3,5,10,25]]
        ))
        v_vals = sorted(set(
            [0] + [int(np.percentile(ad_v, p)) for p in [3,5,10,25]]
            + list(range(0, 10001, 1000))
        ))

        # ── 사전 캐싱: 샘플 배열 기준 ──
        await self._send_status("simulating", 53, "샘플 마스크 사전 캐싱 중...")
        s_f_masks = {f: s_followers >= f for f in f_vals}
        s_l_masks = {l: s_likes >= l for l in l_vals}
        s_v_masks = {v: s_views >= v for v in v_vals}

        # ══════════════════════════════════════════════
        # 패턴 F: 기존 1위 + 날짜 보완 (가장 빠름)
        # ══════════════════════════════════════════════
        if "F" not in skip_patterns:
            await self._send_status("simulating", 55, "패턴F: 기존1위 + 날짜보완 탐색 시작...")

            # 기존 1위 조건 고정 (샘플 기준)
            base_keep = (s_followers >= 3520) | ((s_followers >= 2413) & (s_likes >= 3)) | (s_views >= 10000)

            for dc in date_cuts:
                recent = s_date_masks[dc]
                for f in f_vals:
                    for l in l_vals:
                        _progress_counter[0] += 1
                        keep = base_keep | (recent & s_f_masks[f] & s_l_masks[l])
                        ad_kept = keep[s_ad_mask].sum()
                        recall = ad_kept / S_N_AD
                        if recall < 0.95:
                            continue
                        drop = 1 - keep.sum() / S_N

                        where = (
                            f"(b.followers >= 3520)\n"
                            f"        OR (b.followers >= 2413 AND a.likes >= 3)\n"
                            f"        OR a.views >= 10000\n"
                            f"        OR (a.publish_date >= '{dc}' AND b.followers >= {f} AND a.likes >= {l})"
                        )

                        await _emit({
                            "method": "F:기존+날짜",
                            "condition": f"기존1위 OR (날짜>={dc} & F>={f:,} & L>={l})",
                            "recall": round(float(recall), 4),
                            "drop_rate": round(float(drop), 4),
                            "ad_kept": int(ad_kept),
                            "total_kept": int(keep.sum()),
                            "sql": build_verification_sql(where, f"F: 기존1위+날짜>={dc}"),
                        })
            skip_patterns.add("F")
            _save_now()

        await self._send_status("simulating", 65, f"패턴F 완료 ({total_found:,}개, 최고 {best_drop*100:.1f}%)")

        # ══════════════════════════════════════════════
        # 패턴 G: 날짜 × Followers × Likes 3차원 티어
        # ══════════════════════════════════════════════
        if "G" not in skip_patterns:
            await self._send_status("simulating", 65, "패턴G: 날짜×Followers×Likes 3차원 탐색 시작...")

            f_high_vals = [3000, 5000, 7000, 10000, 15000, 20000]
            f_mid_vals = [1000, 2000, 3000, 4000, 5000]
            l_low_vals = [50, 100, 150, 200, 300, 500]

            for dc in date_cuts:
                recent = date_masks[dc]
                for f_high in f_high_vals:
                    fh_pass = followers >= f_high
                    for f_mid in [x for x in f_mid_vals if x < f_high]:
                        fm_pass = followers >= f_mid
                        for l_low in l_low_vals:
                            for v in v_vals:
                                await _progress("G", 75)
                                keep = (
                                    fh_pass                           # 대형: 무조건
                                    | (fm_pass & recent)              # 중형+최근
                                    | (likes >= l_low)                # 반응 좋은
                                    | (views >= v)                    # 조회수
                                )
                                ad_kept = keep[ad_mask].sum()
                                recall = ad_kept / N_AD
                                if recall < 0.95:
                                    continue
                                drop = 1 - keep.sum() / N

                                where = (
                                    f"b.followers >= {f_high}\n"
                                    f"        OR (b.followers >= {f_mid} AND a.publish_date >= '{dc}')\n"
                                    f"        OR a.likes >= {l_low}\n"
                                    f"        OR a.views >= {v}"
                                )

                                await _emit({
                                    "method": "G:날짜×F×L",
                                    "condition": f"F>={f_high:,} OR (F>={f_mid:,}&날짜>={dc}) OR L>={l_low:,} OR V>={v:,}",
                                    "recall": round(float(recall), 4),
                                    "drop_rate": round(float(drop), 4),
                                    "ad_kept": int(ad_kept),
                                    "total_kept": int(keep.sum()),
                                    "sql": build_verification_sql(where, f"G: 날짜×F×L"),
                                })
            skip_patterns.add("G")
            _save_now()

        await self._send_status("simulating", 80, f"패턴G 완료 ({total_found:,}개, 최고 {best_drop*100:.1f}%)")

        # ══════════════════════════════════════════════
        # 패턴 E: 시간 구간별 다른 기준 (본격)
        # ══════════════════════════════════════════════
        if "E" not in skip_patterns:
            await self._send_status("simulating", 80, "패턴E: 시간구간별 다른기준 탐색 시작...")

            # 2구간: 최근 vs 오래된
            # 최근: (날짜 >= dc AND (F >= f1 OR L >= l1))
            # 오래된: (F >= f2 AND L >= l2) OR V >= v
            f_recent = sorted(set(list(range(0, 10001, 1000)) + [int(np.percentile(ad_f, p)) for p in [3,5,10]]))
            l_recent = [0, 1, 3, 5, 10, 20, 50]
            f_old = sorted(set(list(range(0, 20001, 2000)) + [int(np.percentile(ad_f, p)) for p in [5,10,25]]))
            l_old = sorted(set([0, 5, 10, 20, 50, 100, 200, 500] + [int(np.percentile(ad_l, p)) for p in [5,10,25]]))

            # E용 사전 캐싱 (샘플 기준)
            fr_masks = {fr: s_followers >= fr for fr in f_recent}
            lr_masks = {lr: s_likes >= lr for lr in l_recent}
            fo_masks = {fo: s_followers >= fo for fo in f_old}
            lo_masks = {lo: s_likes >= lo for lo in l_old}
            vo_masks = {v: s_views >= v for v in v_vals}

            for dc in date_cuts:
                recent = s_date_masks[dc]
                old = ~recent
                # 날짜 구간별로 old & vo_masks 사전 계산
                old_v_masks = {v: old & vo_masks[v] for v in v_vals}
                for fr in f_recent:
                    for lr in l_recent:
                        recent_keep = recent & (fr_masks[fr] | lr_masks[lr])
                        recent_ad = recent_keep[s_ad_mask].sum()
                        if recent_ad >= S_N_AD * 0.95:
                            # old 조건 상관없이 recall 충족 — v루프 전체를 최적 drop으로 한번에
                            _progress_counter[0] += len(f_old) * len(l_old) * len(v_vals)
                            best_v_drop = 0
                            best_v_result = None
                            for fo in f_old:
                                for lo in l_old:
                                    old_fo_lo = old & (fo_masks[fo] & lo_masks[lo])
                                    for v in v_vals:
                                        keep = recent_keep | old_fo_lo | old_v_masks[v]
                                        total_kept = keep.sum()
                                        drop = 1 - total_kept / S_N
                                        if drop > best_v_drop:
                                            best_v_drop = drop
                                            ad_kept = keep[s_ad_mask].sum()
                                            recall = ad_kept / S_N_AD
                                            best_v_result = (fo, lo, v, recall, drop, ad_kept, total_kept)
                            if best_v_result and best_v_drop > 0.20:
                                fo, lo, v, recall, drop, ad_kept, total_kept = best_v_result
                                where = (
                                    f"(a.publish_date >= '{dc}' AND (b.followers >= {fr} OR a.likes >= {lr}))\n"
                                    f"        OR\n"
                                    f"        (a.publish_date < '{dc}' AND ((b.followers >= {fo} AND a.likes >= {lo}) OR a.views >= {v}))"
                                )
                                await _emit({
                                    "method": "E:시간구간",
                                    "condition": f"최근({dc}~):F>={fr:,}|L>={lr} / 이전:F>={fo:,}&L>={lo}|V>={v:,}",
                                    "recall": round(float(recall), 4),
                                    "drop_rate": round(float(drop), 4),
                                    "ad_kept": int(ad_kept),
                                    "total_kept": int(total_kept),
                                    "sql": build_verification_sql(where, f"E: 시간구간 {dc}"),
                                })
                            if _progress_counter[0] % 50000 < len(f_old) * len(l_old) * len(v_vals):
                                await _progress_async("E", 90)
                            continue

                        for fo in f_old:
                            old_fo = fo_masks[fo]
                            for lo in l_old:
                                old_fo_lo = old & (old_fo & lo_masks[lo])
                                for v in v_vals:
                                    _progress_counter[0] += 1
                                    keep = recent_keep | old_fo_lo | old_v_masks[v]
                                    ad_kept = keep[s_ad_mask].sum()
                                    recall = ad_kept / S_N_AD
                                    if recall < 0.95:
                                        continue
                                    drop = 1 - keep.sum() / S_N

                                    where = (
                                        f"(a.publish_date >= '{dc}' AND (b.followers >= {fr} OR a.likes >= {lr}))\n"
                                        f"        OR\n"
                                        f"        (a.publish_date < '{dc}' AND ((b.followers >= {fo} AND a.likes >= {lo}) OR a.views >= {v}))"
                                    )

                                    await _emit({
                                        "method": "E:시간구간",
                                        "condition": f"최근({dc}~):F>={fr:,}|L>={lr} / 이전:F>={fo:,}&L>={lo}|V>={v:,}",
                                        "recall": round(float(recall), 4),
                                        "drop_rate": round(float(drop), 4),
                                        "ad_kept": int(ad_kept),
                                        "total_kept": int(keep.sum()),
                                        "sql": build_verification_sql(where, f"E: 시간구간 {dc}"),
                                    })

                                # lo 루프 끝날 때마다 진행률 체크 (v_vals 크기만큼 한번에)
                                if _progress_counter[0] % 50000 < len(v_vals) * 2:
                                    await _progress_async("E", 90)

            skip_patterns.add("E")
            _save_now()

        self.results = combo_results
        await self._send_status("simulated", 98,
            f"E/F/G 완료! {total_tried:,}개 탐색 → {total_found:,}개 유효 (최고 {best_drop*100:.1f}%)")

    # ─── 2단계: 전체 데이터로 상위 결과 검증 ───
    async def verify_top_results(self):
        await self._send_status("verifying", 98, "상위 100개 조합을 전체 데이터로 검증 중...")

        views = self.df["views"].values
        likes = self.df["likes"].values
        comments = self.df["comments"].values
        followers = self.df["followers"].values
        is_reel = self.df["is_reel"].values
        ad_mask = self.df["is_ad"].values == 1
        dates = pd.to_datetime(self.df["publish_date"], errors="coerce").values
        N = len(self.df)
        N_AD = ad_mask.sum()

        # 샘플 기준 상위 100개
        qualified = [r for r in self.results if r.get("recall", 0) >= 0.94]  # 약간 여유
        top100 = sorted(qualified, key=lambda x: x["drop_rate"], reverse=True)[:100]

        verified = []
        for r in top100:
            # SQL의 WHERE 조건을 파이썬으로 재현
            cond = r.get("condition", "")
            method = r.get("method", "")
            sql = r.get("sql", "")

            # WHERE절에서 조건 추출하여 전체 데이터에 적용
            # sql에서 WHERE 이후 부분을 파싱하는 대신, 조건 파라미터를 직접 사용
            # → _emit에서 저장한 파라미터로 재계산
            # 간단한 방법: eval 대신 sql을 기반으로 pandas eval 수행
            # 가장 안전한 방법: 조건문 자체를 저장해두고 여기서 재실행

            # SQL WHERE절을 numpy로 변환 실행
            where_clause = ""
            for line in sql.split("\n"):
                if "WHERE" in line or "CASE" in line:
                    break
                if "SUM(CASE WHEN (" in line:
                    # build_verification_sql에서 WHERE 부분 추출
                    start = line.find("(", line.find("WHEN (")) + 1
                    where_clause = line[start:]
                    break

            # 직접 전체 데이터에서 재계산 (method별 분기)
            try:
                if "E:시간구간" in method:
                    # condition에서 파라미터 추출
                    # "최근(2025-01-01~):F>=3000|L>=5 / 이전:F>=5000&L>=50|V>=5000"
                    parts = cond.split(" / ")
                    recent_part = parts[0]  # "최근(2025-01-01~):F>=3000|L>=5"
                    old_part = parts[1] if len(parts) > 1 else ""

                    dc = recent_part.split("(")[1].split("~")[0]
                    recent_mask = dates >= np.datetime64(dc)
                    old_mask = ~recent_mask

                    # 최근 파라미터
                    r_params = recent_part.split(":")[1]  # "F>=3000|L>=5"
                    fr_val = int(r_params.split("F>=")[1].split("|")[0].replace(",", ""))
                    lr_val = int(r_params.split("L>=")[1].replace(",", ""))
                    recent_keep = recent_mask & ((followers >= fr_val) | (likes >= lr_val))

                    # 이전 파라미터
                    o_params = old_part.split(":")[1] if ":" in old_part else old_part
                    fo_val = int(o_params.split("F>=")[1].split("&")[0].replace(",", ""))
                    lo_val = int(o_params.split("L>=")[1].split("|")[0].replace(",", ""))
                    vo_val = int(o_params.split("V>=")[1].replace(",", ""))
                    old_keep = old_mask & (((followers >= fo_val) & (likes >= lo_val)) | (views >= vo_val))

                    keep = recent_keep | old_keep

                elif "F:기존+날짜" in method:
                    base = (followers >= 3520) | ((followers >= 2413) & (likes >= 3)) | (views >= 10000)
                    dc = cond.split("날짜>=")[1].split(" ")[0].rstrip(")")
                    f_val = int(cond.split("F>=")[1].split(" ")[0].split("&")[0].replace(",", ""))
                    l_val = int(cond.split("L>=")[1].split(")")[0].replace(",", ""))
                    recent_mask = dates >= np.datetime64(dc)
                    keep = base | (recent_mask & (followers >= f_val) & (likes >= l_val))

                elif "G:날짜" in method:
                    parts = cond.split(" OR ")
                    f_high = int(parts[0].split("F>=")[1].replace(",", ""))
                    inner = parts[1]  # "(F>=2000&날짜>=2025-01-01)"
                    f_mid = int(inner.split("F>=")[1].split("&")[0].replace(",", ""))
                    dc = inner.split("날짜>=")[1].split(")")[0]
                    l_low = int(parts[2].split("L>=")[1].replace(",", ""))
                    v_val = int(parts[3].split("V>=")[1].replace(",", ""))
                    recent_mask = dates >= np.datetime64(dc)
                    keep = (followers >= f_high) | ((followers >= f_mid) & recent_mask) | (likes >= l_low) | (views >= v_val)

                else:
                    continue

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
            except Exception:
                # 파싱 실패 시 샘플 결과 그대로 유지
                verified.append({**r, "verified": False})

        self.results = verified
        await self._send_status("verified", 99,
            f"전체 데이터 검증 완료! {len(verified)}개 결과 확정")

    # ─── 전체 파이프라인 실행 ───
    async def run_full_analysis(self):
        try:
            await self.load_data()
            await self.simulate_date_patterns()
            await self.verify_top_results()
            return await self.finalize()
        except Exception as e:
            await self._send("error", {"message": str(e)})
            raise
