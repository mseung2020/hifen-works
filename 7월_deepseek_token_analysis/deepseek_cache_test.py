"""
Temporary test pipeline (DB에 결과를 저장하지 않음):
gpt-4o-mini 대신 DeepSeek 모델로 포스트 ~200개를 분류 호출해보고,
응답의 prompt_cache_hit_tokens / prompt_cache_miss_tokens, 입출력 토큰,
USD 비용을 건별 값 + 평균값으로 JSON에 저장한다.

thinking mode는 최대한 끄도록 요청하지만(extra_body), 이 모델이 실제로
그 파라미터를 지원하는지는 확인되지 않았음 - 응답에 reasoning_content /
reasoning_tokens가 찍히는지로 결과에서 직접 확인할 것.

실행:
    uv run python deepseek_cache_test.py
    uv run python deepseek_cache_test.py --limit 50 --output test.json
"""

import argparse
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from utils.config_loader import get_config
from utils.db_manager import DatabaseManagerFactory
from repositories.post_repository import PostRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
PROMPT_PATH = Path(__file__).parent / "config" / "prompts" / "top-level-classification.txt"
DEFAULT_OUTPUT_PATH = Path(__file__).parent / "deepseek_cache_result_v2.json"

# 1M 토큰당 USD 가격 - deepseek-v4-flash 공식 요금표를 확인하지 못해 비워둠.
# 값을 채우면 각 호출/평균 비용이 자동으로 계산됨. None이면 cost_usd는 null로 출력.
PRICING_USD_PER_1M = {
    "cache_hit_input": 0.0028,
    "cache_miss_input": 0.14,
    "output": 0.28,
}


def fetch_posts(config, limit: int):
    db_manager = DatabaseManagerFactory.create_from_config(config.get("database"))
    post_repo = PostRepository(db_manager, config=config)
    # 이미 분석된 포스트/최근 적재분 제약 없이 넉넉하게 조회 (이번 테스트는 재사용 목적)
    post_repo.lookback_days = 3650
    posts = post_repo.fetch_posts_for_analysis(limit=limit, exclude_analyzed=False)
    return posts[:limit]


def calc_cost_usd(cache_hit_tokens, cache_miss_tokens, output_tokens) -> float | None:
    prices = PRICING_USD_PER_1M
    if any(prices[k] is None for k in ("cache_hit_input", "cache_miss_input", "output")):
        return None
    return (
        (cache_hit_tokens or 0) * prices["cache_hit_input"]
        + (cache_miss_tokens or 0) * prices["cache_miss_input"]
        + (output_tokens or 0) * prices["output"]
    ) / 1_000_000


def call_deepseek(client: OpenAI, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> dict:
    request_kwargs = dict(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    thinking_disable_requested = True
    try:
        response = client.chat.completions.create(
            extra_body={"thinking": {"type": "disabled"}}, **request_kwargs
        )
    except Exception as e:
        logger.warning(f"thinking 비활성화 파라미터가 거부됨 ({e}) - 옵션 없이 재시도")
        thinking_disable_requested = False
        response = client.chat.completions.create(**request_kwargs)

    usage = response.usage.model_dump() if hasattr(response.usage, "model_dump") else dict(response.usage)
    message = response.choices[0].message

    reasoning_content = getattr(message, "reasoning_content", None)
    completion_details = usage.get("completion_tokens_details") or {}
    reasoning_tokens = completion_details.get("reasoning_tokens")

    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    cache_hit_tokens = usage.get("prompt_cache_hit_tokens")
    cache_miss_tokens = usage.get("prompt_cache_miss_tokens")

    return {
        "thinking_disable_requested": thinking_disable_requested,
        "reasoning_content_present": bool(reasoning_content),
        "reasoning_tokens": reasoning_tokens,
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "total_tokens": usage.get("total_tokens"),
        "prompt_cache_hit_tokens": cache_hit_tokens,
        "prompt_cache_miss_tokens": cache_miss_tokens,
        "cost_usd": calc_cost_usd(cache_hit_tokens, cache_miss_tokens, completion_tokens),
    }


def average(records: list, key: str):
    values = [r[key] for r in records if r.get(key) is not None]
    return sum(values) / len(values) if values else None


def main():
    parser = argparse.ArgumentParser(description="DeepSeek prompt cache token 테스트 (DB 저장 없음)")
    parser.add_argument("--limit", type=int, default=200, help="테스트할 포스트 개수 (기본 200)")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_PATH), help="결과 JSON 저장 경로")
    args = parser.parse_args()

    load_dotenv()
    config = get_config()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY가 .env에 없습니다.")

    if any(v is None for v in PRICING_USD_PER_1M.values()):
        logger.warning("PRICING_USD_PER_1M에 가격이 채워지지 않아 cost_usd는 null로 기록됩니다.")

    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL, timeout=60)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    temperature = config.get("llm.temperature", 0.3)
    max_tokens = config.get("llm.max_tokens", 2000)

    logger.info(f"Fetching {args.limit} posts from DB...")
    posts = fetch_posts(config, args.limit)
    logger.info(f"Fetched {len(posts)} posts (requested {args.limit})")

    results = []
    for idx, post in enumerate(posts, 1):
        user_prompt = post.get_analysis_input()
        record = {"post_id": post.post_id}
        try:
            usage = call_deepseek(client, system_prompt, user_prompt, temperature, max_tokens)
            record.update(usage)
            record["success"] = True
            logger.info(
                f"[{idx}/{len(posts)}] post_id={post.post_id} "
                f"input={usage['input_tokens']} output={usage['output_tokens']} "
                f"cache_hit={usage['prompt_cache_hit_tokens']} cache_miss={usage['prompt_cache_miss_tokens']} "
                f"reasoning_present={usage['reasoning_content_present']} "
                f"cost_usd={usage['cost_usd']}"
            )
        except Exception as e:
            record.update({
                "thinking_disable_requested": None,
                "reasoning_content_present": None,
                "reasoning_tokens": None,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "prompt_cache_hit_tokens": None,
                "prompt_cache_miss_tokens": None,
                "cost_usd": None,
                "success": False,
                "error": str(e),
            })
            logger.error(f"[{idx}/{len(posts)}] post_id={post.post_id} failed: {e}")

        results.append(record)

    successful = [r for r in results if r["success"]]

    summary = {
        "model": DEEPSEEK_MODEL,
        "total_requested": len(posts),
        "success_count": len(successful),
        "fail_count": len(results) - len(successful),
        "avg_input_tokens": average(successful, "input_tokens"),
        "avg_output_tokens": average(successful, "output_tokens"),
        "avg_total_tokens": average(successful, "total_tokens"),
        "avg_prompt_cache_hit_tokens": average(successful, "prompt_cache_hit_tokens"),
        "avg_prompt_cache_miss_tokens": average(successful, "prompt_cache_miss_tokens"),
        "avg_reasoning_tokens": average(successful, "reasoning_tokens"),
        "reasoning_content_seen_in_any_call": any(r.get("reasoning_content_present") for r in successful),
        "avg_cost_usd": average(successful, "cost_usd"),
        "total_cost_usd": (
            sum(r["cost_usd"] for r in successful if r.get("cost_usd") is not None)
            if any(r.get("cost_usd") is not None for r in successful)
            else None
        ),
    }

    output = {"summary": summary, "results": results}

    output_path = Path(args.output)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Saved results to {output_path}")
    logger.info("Summary: %s", json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
