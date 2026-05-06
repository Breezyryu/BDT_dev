# 프로파일 / 사이클 탭 — 체크박스 라벨 명확화

- 작성일: 2026-05-07
- 대상: `profile_rest_chk` / `profile_cv_chk` / `chk_coincell_cyc`
- 파일: [DataTool_optRCD_proto_.py](../../DataTool_dev_code/DataTool_optRCD_proto_.py)

## 변경 내역

| 위젯 | 위치 | 변경 전 | 변경 후 |
|---|---|---|---|
| `profile_rest_chk` | 프로파일 탭 데이터 범위 행 2 | `Rest` | **`Rest포함`** |
| `profile_cv_chk` | 프로파일 탭 데이터 범위 행 2 | `CV` | **`CV포함`** |
| `chk_coincell_cyc` | 사이클 탭 통합 모드 행 | `코인셀` | **`코인셀(단위변환)`** |
| `chk_coincell` | 패턴 변경 탭 | `Coin cell` | **`코인셀(단위변환)`** |

setText 위치: [:18358](../../DataTool_dev_code/DataTool_optRCD_proto_.py:18358),
[:18403-18404](../../DataTool_dev_code/DataTool_optRCD_proto_.py:18403),
[:18421](../../DataTool_dev_code/DataTool_optRCD_proto_.py:18421).

## 사이즈 조정

### `chk_coincell_cyc` ([:12923-12924](../../DataTool_dev_code/DataTool_optRCD_proto_.py:12923))

| 차원 | 변경 전 | 변경 후 |
|---|---|---|
| `setMinimumSize` | `(80, 30)` | `(120, 30)` |
| `setMaximumSize` | `(100, 30)` | `(160, 30)` |

### `chk_coincell` ([:13364](../../DataTool_dev_code/DataTool_optRCD_proto_.py:13364))

| 차원 | 변경 전 | 변경 후 |
|---|---|---|
| `setFixedSize` | `(80, 24)` | `(160, 24)` |

폰트 10pt 맑은 고딕 기준 "코인셀(단위변환)" + 체크박스 박스 합쳐
약 130px 필요 → 80px 고정에서는 텍스트 잘림. 안전 마진 확보.

## 의도

- **Rest포함 / CV포함** — 체크박스 ON 의 의미("이 데이터를 *포함* 시킴")
  를 라벨에 명시. 기존 `Rest` / `CV` 만으로는 "Rest 보기 / CV 보기"
  와 혼동 여지 있었음. include_rest / include_cv 파라미터
  ([:2486](../../DataTool_dev_code/DataTool_optRCD_proto_.py:2486),
  [:2275](../../DataTool_dev_code/DataTool_optRCD_proto_.py:2275)) 의 의미와 정확히 일치
- **코인셀(단위변환)** — 체크박스가 단순히 "코인셀 채널" 식별이 아니라
  μA / μAh **단위 변환** 을 트리거 ([:686-696](../../DataTool_dev_code/DataTool_optRCD_proto_.py:686),
  [:11077-11090](../../DataTool_dev_code/DataTool_optRCD_proto_.py:11077)) 한다는 사실을
  라벨에 노출. 인계 시 사용자가 동작을 추론하기 쉬움

## 일관성

세 위젯 모두 μA / μAh **단위 변환** 트리거라는 공통 동작
([:686-696](../../DataTool_dev_code/DataTool_optRCD_proto_.py:686),
[:11077-11090](../../DataTool_dev_code/DataTool_optRCD_proto_.py:11077),
[:34322](../../DataTool_dev_code/DataTool_optRCD_proto_.py:34322)) 을 가지므로
탭 위치 무관하게 라벨 후미 `(단위변환)` 으로 통일.
