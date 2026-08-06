#!/usr/bin/env python3
"""사용법:
    python run.py                  # config.yaml 그대로 실행 (DB 조회 포함)
    python run.py --skip-db        # DB 조회 없이, 이미 받아둔 raw csv로 재계산만
    python run.py --config other.yaml
"""
import argparse

from src.pipeline import run


def main():
    parser = argparse.ArgumentParser(description="브랜드 PPL 비용 리포트 파이프라인")
    parser.add_argument("--config", default=None, help="config.yaml 경로 (기본: ./config.yaml)")
    parser.add_argument("--skip-db", action="store_true", help="DB 조회를 건너뛰고 기존 raw csv로 재계산")
    args = parser.parse_args()

    run(config_path=args.config, skip_db=args.skip_db)


if __name__ == "__main__":
    main()
