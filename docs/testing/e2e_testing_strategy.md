# BDT E2E 테스트 전략 (Plot 결과 검증 포함)

**작성일**: 2026-04-18  
**맥락**: 사내 전용 프로그램을 사외에서 개발 후 사내 이관. 코드 회귀뿐 아니라 **시각 출력(plot)도 회귀 방지** 필요.

## 3-Layer Plot 검증 체계

### 4a. Axes 데이터 검증 (자동, CI 가능)

**도구**: `DataTool_dev_code/test_code/plot_verify.py` (신규)

**장점**: matplotlib Figure 객체만으로 결정적 검증. 빠름, 재현성 있음.

**사용 예**:
```python
@pytest.mark.gui
def test_profile_plot_structure(app_window, pne_ch008):
    # 앱에서 분석 실행
    _run_profile_analysis(app_window, pne_ch008, cycles=[10, 20])
    
    # Figure 추출 + 구조 검증
    fig = extract_current_tab_figure(app_window)
    verify_figure_structure(fig, n_axes=6)
    
    # 첫 subplot: 전압 프로파일
    ax = fig.get_axes()[0]
    verify_axes_has_data(ax, min_lines=2)  # 2개 사이클
    for line in ax.get_lines():
        verify_voltage_range(line, axis='y')  # 2.0~5.0 V
        verify_monotonic(line, axis='x', direction='increasing')  # 시간 단조
```

**커버 범위**:
- 탭 생성 성공
- subplot 개수 정확
- 데이터 포인트 수
- xlim/ylim 범위 (배터리 도메인 규칙: V 2-5, SOC 0-100, I -10C~+10C)
- 단조성, NaN 비율

### 4b. Figure Fingerprint 회귀 (자동, baseline 관리)

**도구**: `plot_verify.compute_fig_fingerprint()` + `compare_fingerprints()`

**패턴**:
```python
# 1회차: baseline 생성
baseline = compute_fig_fingerprint(fig)
json.dump(baseline, open("baselines/profile_gitt.json", "w"))

# 이후: 회귀 비교
expected = json.load(open("baselines/profile_gitt.json"))
actual = compute_fig_fingerprint(fig)
diffs = compare_fingerprints(expected, actual, tol_rel=0.05)
assert not diffs, f"회귀: {diffs}"
```

**장점**: pytest-mpl 없이도 구조적 회귀 감지.

**단점**: "색상/선 스타일/레전드 위치" 같은 순수 시각적 변경은 못 잡음 → 필요 시 pytest-mpl 도입.

**baseline 관리**:
- `tests/baselines/` 에 JSON 저장 (git 추적)
- 의도된 UI 변경 시 `--update-baseline` 플래그로 일괄 갱신

### 4c. computer-use E2E (수동, 릴리스 전 시나리오)

**도구**: computer-use MCP (Claude Code 세션 내) 또는 사용자 수동 실행

**시나리오 정의 형식** (다른 세션에서도 재현 가능):

```yaml
# tests/scenarios/cycle_floating_ch55.yaml
name: "복합floating ch55 사이클 분석 + 프로파일"
environment: external  # external | internal
data_required:
  - path: "exp_data/복합floating/260413_.../M01Ch055[055]"
    required_files: ["*.cyc", "*.sch"]
steps:
  - action: open_app
    command: python DataTool_dev_code/DataTool_optRCD_proto_.py
  - action: click_tab
    tab: "사이클데이터"
  - action: type_path
    target: "경로_테이블_row1_col1"
    value: "{{data_path}}"
  - action: click_button
    name: "채우기"
  - action: verify_cell
    target: "경로_테이블_row1_col4"
    pattern: "1-\\d+"
  - action: click_button
    name: "사이클 분석"
  - action: wait_for_tab_count
    min: 1
    timeout: 30s
  - action: screenshot
    path: "snapshots/cycle_floating_ch55_{{timestamp}}.png"
  - action: switch_subtab
    name: "Profile"
  - action: click_bar
    cycle_no: 5
  - action: click_button
    name: "프로파일 분석"
  - action: screenshot
    path: "snapshots/profile_cy5_{{timestamp}}.png"
  - action: verify_cmd_log
    pattern: "\\[\\.cyc 프로파일\\].*기록시각.*\\d+\\.\\d+h"
post_actions:
  - llm_review_screenshots: "프로파일 그래프 6개 subplot에 데이터가 올바르게 표시됐는지 확인"
expected_outcomes:
  - no_crash: true
  - cmd_log_contains: ["[.cyc 보충]", "기록시각:"]
  - tab_count_after_cycle: ">= 1"
  - tab_count_after_profile: ">= 2"
```

**실행 방식**:
- 개발자가 특정 시나리오 파일 지정 → Claude Code 에이전트에게 "이 시나리오 실행해줘" 요청
- 에이전트가 computer-use로 실제 조작 + 스크린샷 수집
- 스크린샷을 Claude가 `llm_review_screenshots` 단계에서 검토
- 결과 리포트 생성

**제약**:
- 에이전트 세션이 사용자 화면을 점유 (작업 중 불가)
- 느림 (시나리오 1개당 1~5분)
- 용도: 릴리스 전, 큰 변경 후 핵심 시나리오만

## 환경별 실행 매트릭스

| 테스트 | 사외 CI/로컬 | 사외 수동 | 사내 수동 |
|--------|:-----------:|:--------:|:---------:|
| L0 Syntax | ✅ 매 커밋 | ✅ | ✅ |
| L1 단위 | ✅ 매 커밋 | ✅ | ✅ |
| L2 통합 (샘플 데이터) | ✅ 매 커밋 | ✅ | ✅ |
| L3 GUI 스모크 | ✅ 매 커밋 (Win) | ✅ | ✅ |
| **4a Axes 검증** | ✅ 매 커밋 (Win) | ✅ | ✅ |
| **4b Fingerprint** | ✅ 매 커밋 | ✅ | ✅ |
| **4c computer-use E2E** | ❌ (점유) | ✅ 릴리스 전 | ✅ 이관 후 |
| L5 실 대용량 데이터 | ❌ (데이터 없음) | ❌ | ✅ 주요 시나리오 |

## 사내 이관 체크리스트 (plot 포함)

```
□ L0~L2 사외 CI PASS
□ L3~4b 사외 수동 PASS (최소 대표 시나리오 3개)
□ 4c 사외 E2E 스크린샷 리뷰 완료
□ 신규 Figure baseline 등록 (4b)
□ 사내 이관 후 동일 시나리오 L5 재실행
□ 사내 스크린샷과 사외 baseline 육안 비교 1회
```

## 시나리오 라이브러리 (초안)

- `cycle_floating_ch55.yaml` — 프로파일 분석 + .cyc 보충 로그 검증
- `cycle_large_dataset_ch30.yaml` — 대용량(1202사이클) 플롯 렌더링
- `profile_hysteresis.yaml` — 히스테리시스 모드 Profile
- `profile_sweep_gitt.yaml` — GITT 스윕 TC 매핑
- `status_filter_v3.yaml` — 현황 탭 v3 상태 분류
- `ect_pattern_edit.yaml` — 패턴수정 탭 편집 → 저장
- `dvdq_analysis.yaml` — dVdQ 분석 + CV 마스킹

각 시나리오는 독립적으로 실행 가능하며, 장기적으로 **회귀 risk가 높은 것부터** 자동화.

## 다음 단계

1. **4a 샘플 테스트 작성** → 프로파일 분석 Figure 구조 검증 (즉시)
2. **4b baseline 생성** → 현재 PASS하는 4a 테스트의 fingerprint를 baseline으로 저장
3. **4c 시나리오 1개 파일화** → `cycle_floating_ch55.yaml`
4. **CI 스크립트** → `.github/workflows/test.yml` 또는 `scripts/run_tests.ps1` (L0-4b 자동)
