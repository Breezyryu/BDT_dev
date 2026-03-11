# 연결 Cycle 전처리(Pre-processing) 리팩토링

## 날짜
2026-03-12

## 변경 파일
- `DataTool_dev/DataTool_optRCD_proto_.py` — `link_cyc_confirm_button` 함수

## 변경 내용

### 문제
- 연결(Link) 사이클 모드에서 동일 채널의 데이터셋이 여러 폴더에 걸쳐 있을 때, 각 폴더 데이터를 개별적으로 `graph_output_cycle`에 전달하여 DC-IR 등의 선(plot) 그래프가 데이터셋 사이에서 끊어지는 현상 발생.

### 해결 (전처리 방식 — 2단계 구조)
기존 단일 루프(로딩+플롯 동시)를 **2단계**로 분리:

1. **1단계 — 수집 + 엑셀 출력**
   - 기존과 동일하게 폴더별 데이터 로딩, index 오프셋 적용, 엑셀 출력 수행.
   - 동시에 `merged` 딕셔너리에 `sub_label` 기준으로 DataFrame을 누적 수집.
   - `merged = {sub_label: {'frames': [df1, df2, ...], 'colorno': int, 'ch_label': str}}`

2. **2단계 — 병합 후 플롯**
   - `merged` 딕셔너리를 순회하며 같은 채널의 DataFrame들을 `pd.concat → sort_index`로 병합.
   - 병합된 단일 DataFrame을 wrapper 객체에 감싸서 `graph_output_cycle`에 1회만 전달.
   - 개별(indiv) 모드와 동일한 데이터 구조 → 선 그래프 연결 유지.

### 효과
- DC-IR 등 `ax4.plot()` 선이 데이터셋 경계에서 끊어지지 않고 연속으로 표시됨.
- 개별 모드와 연결 모드의 데이터셋 구조가 동일해짐.
- 엑셀 출력은 기존과 동일하게 폴더 단위로 유지.
