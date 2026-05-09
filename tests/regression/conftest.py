"""regression 측 pytest 설정 — --update-baseline flag."""
from __future__ import annotations


def pytest_addoption(parser):
    parser.addoption(
        "--update-baseline", action="store_true", default=False,
        help="baseline 재생성 (회귀 비교 X)"
    )
