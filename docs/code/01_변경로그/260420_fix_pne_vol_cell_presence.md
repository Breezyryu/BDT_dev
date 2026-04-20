# 260420 PNE 현황/필터링 탭 — vol 기반 셀있음/셀없음 구분 추가

## 배경 / 목적

### 이전 상태의 불일치
같은 유휴 상태(완료/대기/준비/작업정지)라도 **물리적으로 셀이 장착됐는지**
여부를 시각적으로 구분할 수 있어야 하는데, Toyo 와 PNE 간 로직이 달랐음:

| 경로 | 이전 동작 | 문제 |
|---|---|---|
| Toyo 현황 탭 | vol 기반 (원본 유지) | — |
| PNE 현황 탭 | **vol 무시**, use 만으로 색 결정 | 완료+셀없음 채널도 연녹 표시 |
| 필터링 탭 | **vol 무시**, STATUS_BG dict lookup | 동일 |
| 요약 카운트 | vol 기반 (idle_no_cell / idle_has_cell) | 색상과 숫자 불일치 |

결과: PNE 현황 탭에서 "완료"된 모든 채널이 연녹으로 표시되어 **셀 회수
완료된 슬롯**과 **아직 셀이 남아있는 슬롯**을 색만 보고 구분할 수 없음.
요약바는 셀 유무로 나뉘어 표시되므로 **숫자와 색이 안 맞는** 현상 발생.

### 판정 기준
`vol` 컬럼 값으로 판정 (원본 규칙 그대로):
- `vol == "-"` → 셀없음 (PNE: Voltage ≤ 0.04V / Toyo: 2V 미만 또는 5V 초과)
- `vol != "-"` → 셀있음 (정상 전압 측정)

---

## 변경 내용

### 1. PNE 현황 탭 (`pne_table_make`)
**파일**: `DataTool_dev_code/DataTool_optRCD_proto_.py` (line 25492~25511)

**Before**
```python
bg_level = 0
use_val = self.df.loc[i + (j - 1) * num_i, "use"]
self.tb_channel.item(j - 1, i - 1).setBackground(QtGui.QColor(246,246,243))
if use_val in ("대기", "준비"):
    → 녹(176,203,176)    bg_level=1
elif use_val == "완료":
    → 연녹(234,239,230)  bg_level=2
elif use_val not in self._NORMAL_STATES:
    if use_val == "사용자멈춤" or use_val.startswith("중단점 도달"):
        → 노랑(240,220,160) bg_level=4
    else:
        → 빨강(214,155,154) bg_level=3
```

**After**
```python
bg_level = 0
use_val = self.df.loc[i + (j - 1) * num_i, "use"]
vol_val = self.df.loc[i + (j - 1) * num_i, "vol"]
self.tb_channel.item(j - 1, i - 1).setBackground(QtGui.QColor(246,246,243))
# 유휴 상태 (완료/대기/준비/작업정지) — vol 기반 셀있음/셀없음 구분
if use_val in ("완료", "대기", "준비", "작업정지"):
    if vol_val == "-":
        → 녹(176,203,176)    bg_level=1  # 셀없음
    else:
        → 연녹(234,239,230)  bg_level=2  # 셀있음
elif use_val not in self._NORMAL_STATES:
    if use_val == "사용자멈춤" or use_val.startswith("중단점 도달"):
        → 노랑(240,220,160) bg_level=4
    else:
        → 빨강(214,155,154) bg_level=3
```

변경 요약:
- `vol_val` 읽어오기 추가
- 유휴 상태 분기 통합: `("완료", "대기", "준비", "작업정지")` 하나로 묶고
  vol 유무로 녹/연녹 분기
- `"작업정지"` 추가 — 이전에는 이 상태에서 기본색이었으나 이제 유휴 처리

### 2. 필터링 탭 렌더 루프 (`filter_all_channels`)
**파일**: 동일 (line ~26558)

**Before**
```python
for ch_no, testname, status, elapsed_str, cyc, vol, type_str, temp_str, cell_path in channels:
    bg_color = STATUS_BG.get(status)
    status_base = status.split(" (")[0] if " (" in status else status
    # STATUS_BG 미매칭 + 비정상 상태 → 3색 분기
    ...
```

**After**
```python
for ch_no, testname, status, elapsed_str, cyc, vol, type_str, temp_str, cell_path in channels:
    bg_color = STATUS_BG.get(status)
    status_base = status.split(" (")[0] if " (" in status else status
    # 유휴 상태 (완료/시험완료/대기/준비/작업정지) — vol 기반 셀있음/셀없음 override
    # _IDLE_BG(녹)=셀없음, _COMPLETED_BG(연녹)=셀있음 로 통일
    if bg_color in (_IDLE_BG, _COMPLETED_BG):
        bg_color = _COMPLETED_BG if vol != "-" else _IDLE_BG
    # STATUS_BG 미매칭 + 비정상 상태 → 3색 분기
    ...
```

STATUS_BG 딕셔너리 자체는 건드리지 않고, lookup 결과가 유휴 색상(_IDLE_BG /
_COMPLETED_BG) 중 하나이면 vol 기준으로 덮어쓰기.

---

## 영향 범위

### 동작 변화 매트릭스

| 상태 | vol | v4 색상 | v5 색상 |
|---|---|---|---|
| 완료 | 정상값 | 연녹 (셀있음) | 연녹 (셀있음) — 동일 |
| 완료 | `-` | 연녹 (잘못) | **녹 (셀없음)** |
| 대기/준비 | 정상값 | 녹 (잘못) | **연녹 (셀있음)** |
| 대기/준비 | `-` | 녹 (셀없음) | 녹 (셀없음) — 동일 |
| 작업정지 | 정상값 | 기본색 | **연녹 (셀있음)** |
| 작업정지 | `-` | 기본색 | **녹 (셀없음)** |
| 시험완료 (필터링 탭) | 정상값 | 연녹 | 연녹 — 동일 |
| 시험완료 (필터링 탭) | `-` | 연녹 | **녹** |
| 작업중/충전/방전/진행/휴지 | 무관 | 기본색 | 기본색 — 동일 |
| 사용자멈춤/중단점 도달 | 무관 | 노랑 | 노랑 — 동일 |
| 챔버이슈/작업멈춤 etc | 무관 | 빨강/노랑 | 빨강/노랑 — 동일 |

### 요약 카운트와의 정합성
이제 PNE 현황 탭·필터링 탭 색상이 `idle_no_cell` / `idle_has_cell`
카운트와 **색-숫자 일관성** 확보:
- `idle_no_cell` 에 잡힌 채널 → 화면에 녹색 표시
- `idle_has_cell` 에 잡힌 채널 → 화면에 연녹색 표시

### 회귀 체크 포인트 (사내 환경)
1. **PNE 완료+셀없음** 채널 → 녹색으로 표시되는지
2. **PNE 대기/준비+셀있음** 채널 → 연녹색으로 표시되는지 (이상 상황 경고)
3. **Toyo** 현황 탭 → 기존 동작 유지 (이번 변경 대상 아님)
4. **멈춤 계열** (작업멈춤/사용자멈춤/중단점 도달/챔버이슈) → 노랑/빨강 유지
5. **작업중/충전/방전/진행/휴지** → 기본색 유지
6. **요약바** 숫자와 화면 색상이 일치하는지
