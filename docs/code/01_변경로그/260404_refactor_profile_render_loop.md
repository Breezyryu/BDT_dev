# 260404 — 프로필 분석 6개 버튼 중 4개 → `_profile_render_loop()` 통합 리팩토링

**날짜**: 2026-04-04
**대상 파일**: `DataTool_dev/DataTool_optRCD_proto_.py`
**카테고리**: 리팩토링

---

## 1. 배경 / 목적

사이클데이터 탭(Tab 1)의 프로필 분석 버튼 6개(`step_confirm_button`, `chg_confirm_button`, `rate_confirm_button`, `dchg_confirm_button`, `continue_confirm_button`, `dcir_confirm_button`)는 **동일한 3-모드 렌더링 루프**(CycProfile / CellProfile / AllProfile)를 각자 200~280줄씩 복사하여 사용하고 있었다.

이 중복은 다음 문제를 야기했다:
- 모드 분기 로직 변경 시 6곳 동시 수정 필요 → **동기화 누락 위험**
- 전체 코드량 ~1,500줄 중 실제 고유 로직은 각 버튼당 20~40줄 → **코드 대비 정보 밀도 낮음**
- 신규 모드 추가(예: CompareProfile) 시 6곳에 모두 분기 추가 필요

**목표**: 공통 3-모드 루프를 `_profile_render_loop()`로 추출하고, 각 버튼은 자기만의 플롯/데이터 로직만 콜백으로 전달하는 **Strategy Pattern** 적용.

---

## 2. 변경 전 / 변경 후 비교

### 구조 비교

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| `step_confirm_button()` | ~205줄 (3-모드 루프 인라인) | ~40줄 (콜백 정의 + `_profile_render_loop()` 호출) |
| `rate_confirm_button()` | ~260줄 | ~70줄 |
| `chg_confirm_button()` | ~280줄 | ~70줄 |
| `dchg_confirm_button()` | ~280줄 | ~65줄 |
| `_profile_render_loop()` | 없음 (신규) | ~200줄 |
| **합계** | ~1,025줄 | ~445줄 (**56% 감소**) |

### 코드 흐름 비교

**변경 전** (각 버튼 내부):
```
confirm_button():
    init_data = _init_confirm_button()
    loaded_data = _load_all_*_parallel()

    if CycProfile:
        for ch in channels:
            fig, axes = create_figure()
            for cyc in cycles:
                temp = loaded_data[ch][cyc]
                # --- 버튼별 고유 플롯 로직 (20~40줄) ---
            finalize(fig)
            add_tab(fig)
    elif CellProfile:
        for cyc in cycles:
            fig, axes = create_figure()
            for ch in channels:
                # --- 동일한 고유 플롯 로직 반복 ---
            finalize(fig)
            add_tab(fig)
    elif AllProfile:
        fig, axes = create_figure()
        for ch in channels:
            for cyc in cycles:
                # --- 또 동일한 고유 플롯 로직 반복 ---
        finalize(fig)
        add_tab(fig)
```

**변경 후**:
```
confirm_button():
    init_data = _init_confirm_button()
    loaded_data = _load_all_*_parallel()

    def plot_one_fn(temp, axes, ...):
        # 버튼별 고유 플롯 로직만 정의 (20~40줄)
        return (writecolno, artists)

    def fallback_fn(folder, cyc, is_pne):
        # 개별 로딩 폴백 로직
        return data

    self._profile_render_loop(
        loaded_data=..., plot_one_fn=plot_one_fn,
        fallback_fn=fallback_fn, data_attr="stepchg", ...)
```

---

## 3. 신규 함수: `_profile_render_loop()`

### 위치
`DataTool_optRCD_proto_.py` — 약 12621줄 부근

### 시그니처

```python
def _profile_render_loop(
    self, *,
    loaded_data: dict,
    all_data_folder: list,
    all_data_name: list,
    CycleNo: list,
    writer,
    save_file_name: str | None,
    plot_one_fn,          # 콜백: (temp, axes, headername, lgnd, temp_lgnd,
                          #         writer, save_file_name, writecolno, CycNo)
                          #       → (new_writecolno, artists_list)
    fallback_fn,          # 콜백: (FolderBase, CycNo, is_pne) → data
    data_attr: str,       # temp[1]에서 유효성 체크할 속성명
    legend_positions: list[str],
    axes_order: list[int] | None = None,  # subplot 축 순서 (기본: [0,1,3,2,4,5])
    figsize: tuple[int, int] = (14, 10),
) -> None:
```

### 주요 파라미터 설명

| 파라미터 | 역할 |
|---------|------|
| `plot_one_fn` | 하나의 (채널, 사이클) 조합에 대한 플롯 + 저장 로직. 각 버튼이 클로저로 정의 |
| `fallback_fn` | 병렬 로딩 실패 시 개별 재로딩 함수 |
| `data_attr` | `temp[1]`(데이터 객체)의 속성명. 유효성 체크에 사용 (예: `"stepchg"`, `"Profile"`, `"rateProfile"`) |
| `axes_order` | subplot 축 재배열 순서. step은 `[0,1,3,2,4,5]` (ax3↔ax4 스왑), 나머지는 `[0,1,2,3,4,5]` |
| `legend_positions` | 6개 subplot 각각의 범례 위치 |

---

## 4. 변환된 4개 버튼별 콜백 특성

| 버튼 | 콜백 함수 | data_attr | axes_order | 특이사항 |
|------|----------|-----------|------------|---------|
| `step_confirm_button` | `_step_plot_one` | `"stepchg"` | 기본값 `[0,1,3,2,4,5]` | `_plot_and_save_step_data()` 재사용 |
| `rate_confirm_button` | `_rate_plot_one` | `"rateProfile"` | `[0,1,2,3,4,5]` | 6개 `graph_step()` 호출, `capacitytext` 업데이트 |
| `chg_confirm_button` | `_chg_plot_one` | `"Profile"` | `[0,1,2,3,4,5]` | `chk_dqdv` 토글로 dQ/dV 축 방향 전환 |
| `dchg_confirm_button` | `_dchg_plot_one` | `"Profile"` | `[0,1,2,3,4,5]` | 방전 dQ/dV 스케일 음수 방향 |

---

## 5. 개발 중 수정 이력

### 수정 1: 콜백 계약 변경 (data_obj → temp)

- **문제**: 최초 설계에서 `plot_one_fn`에 `data_obj = getattr(temp[1], data_attr)` 만 전달
- **원인**: `step_confirm_button`은 `temp[0]`(capacity)과 `temp[1].stepchg` 모두 필요
- **해결**: 3개 호출 지점 모두 `temp` 튜플 전체를 콜백에 전달하도록 변경

### 수정 2: axes_order 파라미터 추가

- **문제**: `_profile_render_loop()` 내부에 `[axes[0], axes[1], axes[3], axes[2], axes[4], axes[5]]` 하드코딩
- **원인**: step 프로필은 ax3↔ax4 스왑 필요하나, rate/chg/dchg는 자연 순서 사용
- **해결**: `axes_order` 매개변수 추가 (기본값 `[0,1,3,2,4,5]`), 5곳 하드코딩을 `[axes[k] for k in axes_order]`로 교체

---

## 6. 영향 범위

| 영향 대상 | 변경 유형 | 설명 |
|----------|----------|------|
| `step_confirm_button()` | 대폭 축소 | ~205줄 → ~40줄 |
| `rate_confirm_button()` | 대폭 축소 | ~260줄 → ~70줄 |
| `chg_confirm_button()` | 대폭 축소 | ~280줄 → ~70줄 |
| `dchg_confirm_button()` | 대폭 축소 | ~280줄 → ~65줄 |
| `_profile_render_loop()` | 신규 | ~200줄, 3-모드 공통 루프 |
| `continue_confirm_button()` | **미변경** | 이번 스코프 외 |
| `dcir_confirm_button()` | **미변경** | 이번 스코프 외 |
| UI / 사용자 동작 | **동일** | 기능 변화 없음 (순수 리팩토링) |

---

## 7. 미완료 / 후속 작업

- `continue_confirm_button()` — 동일 패턴 적용 가능하나 이번 스코프에서 제외
- `dcir_confirm_button()` — 동일 패턴 적용 가능하나 이번 스코프에서 제외
- 런타임 테스트 — 실제 데이터로 4개 버튼 정상 동작 확인 필요
