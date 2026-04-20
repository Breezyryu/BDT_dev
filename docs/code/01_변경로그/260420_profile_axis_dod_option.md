# 프로파일 X축 DOD 옵션 추가

날짜: 2026-04-20
파일: `DataTool_dev_code/DataTool_optRCD_proto_.py`

## 배경

실무 경로 예시 `0.5C-10min volt hysteresis`:
- cycle 3-12 구간: **SOC 축** 히스테리시스
- cycle 14-23 구간: **DOD 축** 히스테리시스 (방전 심도 기준)

기존 BDT 프로파일 축 옵션은 `SOC / 시간` 두 개뿐이라, 같은 히스테리시스 데이터를 DOD 좌표계로 보려면 외부 툴에서 재가공이 필요했다. 축 버튼에 **DOD** 를 추가해 UI 토글만으로 좌표계 전환을 지원.

## 변경 내용

### 1. UI — 축 버튼 3개화 (L11344~L11353)

```python
# Before: ["SOC(DOD)", "시간"] (2버튼)
# After:  ["SOC", "DOD", "시간"] (3버튼, id: 0=SOC, 1=DOD, 2=시간)
_axis_seg, _axis_btns = self._make_seg_group(
    ["SOC", "DOD", "시간"], ..., checked_idx=2)
self.profile_axis_soc = _axis_btns[0]
self.profile_axis_dod = _axis_btns[1]
self.profile_axis_time = _axis_btns[2]
```

### 2. 옵션 수집 (L24107~L24151)

```python
axis_map = {0: "soc", 1: "dod", 2: "time"}
axis_mode = axis_map.get(self.profile_axis_group.checkedId(), "soc")
...
calc_dqdv = (axis_mode in ("soc", "dod"))  # DOD도 좌표 기반 dQ/dV 계산 가능
```

### 3. 프리셋 매핑 (L23315)

```python
axis_id = {"soc": 0, "dod": 1, "time": 2}[axis]
```

### 4. overlap/axis 제약 (L23228-L23240)

| overlap | SOC | DOD | 시간 |
|---|---|---|---|
| 이어서 | ✗ | ✗ | ✓ |
| 분리 | ✓ | ✓ | ✓ |
| 연결(히스테리시스) | ✓ | ✓ | ✗ |

### 5. `_calc_soc` DOD 분기 (L2076~)

**히스테리시스 DOD (연결 + DOD):**
- 방전: `DchgCap` (0 → 방전량)
- 충전: `-ChgCap` (-1 → 0), 대칭 음수 영역
- 결과: 모든 cycle 방전 곡선이 x=0 에서 시작하여 각자 방전량까지 → 이미지와 동일

**분리 DOD (split + DOD):**
- 방전: `DchgCap` (0 → 1)
- 충전: `-ChgCap` (-1 → 0)

검증:
```
cycle 3 (SOC 100%→40% 방전):
  충전 구간:    ChgCap=0.0→1.0   → SOC=0→1      DOD=0→-1
  방전 구간:    DchgCap=0.0→0.6  → SOC=1→0.4    DOD=0→0.6
cycle 4 (SOC 80%→30% 방전):
  충전 구간:    ChgCap=0.0→0.8   → SOC=0→0.8    DOD=0→-0.8
  방전 구간:    DchgCap=0.0→0.5  → SOC=0.8→0.3  DOD=0→0.5
```

### 6. 히스테리시스 offset 스킵 (L24306)

DOD 축은 모든 cycle이 x=0 에서 시작하므로 `_apply_hysteresis_soc_offsets` 불필요 → SOC 축일 때만 호출.

### 7. 히스테리시스 플롯 라벨 + X축 범위 (L24446~L24549)

```python
_axis_label = "DOD" if options.get('axis_mode') == 'dod' else "SOC"
_is_dod = (options.get('axis_mode') == 'dod')
_x_lo, _x_hi = (-1.1, 1.2) if _is_dod else (-0.1, 1.2)
```

DOD 모드에서 x축 -1.1 ~ 1.2 범위로 확대 (충전 음수 영역 포함).
모든 graph_profile 호출에서 x 라벨 / 범위가 축 모드에 따라 동적 전환.

### 8. legacy_mode 라우팅 (L24173)

SOC / DOD 모두 같은 `cycle_soc` / `dchg` / `chg` 경로로 라우팅. 축별 분기는 `_calc_soc` + 플롯 라벨 수준에서 처리.

## 실무 워크플로우

```
[히스테리시스 프리셋 선택]
  → scope=사이클, overlap=연결, axis=SOC 기본 (프리셋은 SOC 유지)
  → 축 버튼에서 DOD 선택 시 같은 데이터를 DOD 좌표로 즉시 재그림
  → 레인보우 색상(260420 이전 변경)은 두 축 모두 동일 적용
```

cycle 3-12 (SOC 축 히스테리시스) 분석 완료 후 축 버튼만 DOD 로 전환 → cycle 14-23 DOD 분석 동일 워크플로우로 수행 가능.

## 영향 범위

- UI 버튼 1개 추가 (`profile_axis_dod`).
- `_calc_soc` 분기 확장, 기존 SOC/시간 동작 변경 없음.
- `_map_options_to_legacy_mode` SOC → SOC/DOD 허용으로 범위 확장.
- 히스테리시스 플롯 x축 라벨/범위가 축 모드 감응.
- 기존 파이프라인(충전/방전 단방향, 시간축, 연결 SOC) 모든 조합 회귀 없음.

## 검증 포인트

- [ ] UI: 축 버튼이 SOC / DOD / 시간 3개로 표시
- [ ] 프리셋 히스테리시스 선택 → SOC 축 자동 선택
- [ ] 연결(히스테리시스) overlap → SOC/DOD 둘 다 활성, 시간 비활성
- [ ] 분리 overlap → SOC/DOD/시간 모두 활성
- [ ] 이어서 overlap → SOC/DOD 비활성, 시간 강제
- [ ] 히스테리시스 + SOC 축 → cycle 3-12 기존 그래프 동일 (레인보우 색상)
- [ ] 히스테리시스 + DOD 축 → cycle 14-23 이미지와 동일 형태 (방전 라인이 x=0 에서 시작)
- [ ] DOD 축 x축 라벨이 "DOD" 로 표시
- [ ] 방전 프리셋 + SOC/DOD 모두 dQ/dV 계산 정상
