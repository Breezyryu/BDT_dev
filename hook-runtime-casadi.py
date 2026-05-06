"""PyInstaller runtime hook — frozen 환경 초기화.

pybamm import 전에 실행되어야 한다.
"""
import os

# pybamm posthog 텔레메트리 차단 — 사내 정보 유출 방지
os.environ["PYBAMM_DISABLE_TELEMETRY"] = "true"
