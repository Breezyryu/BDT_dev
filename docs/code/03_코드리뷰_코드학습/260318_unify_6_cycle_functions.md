# Cycle 6개 함수 → 1개 통합 함수 변경 로그

## 날짜
2026-03-18

## 변경 파일
- `DataTool_dev/DataTool_optRCD_proto_.py`

## 변경 요약

### 삭제된 함수 (6개)
| 함수 | 역할 |
|------|------|
| `app_cyc_confirm_button` | 신뢰성 Cycle (.xlsx) |
| `indiv_cyc_confirm_button` | 개별 Cycle (폴더별 1탭) |
| `overall_cyc_confirm_button` | 통합 Cycle (모든 폴더 1탭) |
| `link_cyc_confirm_button` | 연결 Cycle (채널별 병합) |
| `link_cyc_indiv_confirm_button` | 연결 Cycle 여러개 개별 (파일별 1탭) |
| `link_cyc_overall_confirm_button` | 연결 Cycle 여러개 통합 (전체 1탭) |
| `app_pne_path_setting` | 미사용 헬퍼 (삭제) |

### 추가된 함수
| 함수 | 역할 |
|------|------|
| `_parse_path_file(filepath)` | .txt path 파일 파싱 (static) |
| `_build_group_from_lines(lines, file_idx)` | 직접입력 줄→CycleGroup 변환 |
| `_parse_cycle_input()` | 3가지 입력 모드 통합 파싱 → `list[CycleGroup]` |
| `unified_cyc_confirm_button()` | 통합 사이클 분석 메인 함수 |

### CycleGroup dataclass 변경
- `path_names` 필드 추가 (per-path cyclename)
- `source_file` 필드 추가 (원본 파일 경로, mAh 추출용)

### UI 변경 (setupUi)
- **삭제**: 6개 버튼 (`indiv_cycle`, `overall_cycle`, `link_cycle`, `AppCycConfirm`, `link_cycle_indiv`, `link_cycle_overall`)
- **삭제**: `horizontalLayout_92` (3번째 버튼 행)
- **추가**: `radio_indiv` (개별 라디오, 기본 선택)
- **추가**: `radio_overall` (통합 라디오)
- **추가**: `chk_link_cycle` (연결처리 체크박스)
- **추가**: `cycle_confirm` (Cycle 분석 버튼, 430x70)

### retranslateUi 변경
- 6개 버튼 텍스트 → 3개 위젯 텍스트 (`개별`, `통합`, `연결처리`, `Cycle 분석`)

### connect 변경
- 6개 `.clicked.connect()` → 1개 `cycle_confirm.clicked.connect(unified_cyc_confirm_button)`

## 통합 동작 규칙

### 입력 모드별 동작
| 입력 방식 | 연결처리 체크박스 | 동작 |
|-----------|-----------------|------|
| 지정Path (.xlsx) | 무관 | 신뢰성 모드 (1x1, ax1만) |
| 지정Path (.txt) | 무관 | cyclename 동일 = 자동 연결 |
| 직접입력 | ✅ ON | 빈줄 없이 연속 = 연결, 빈줄 = 구분 |
| 직접입력 | ❌ OFF | 모든 줄 = 개별 |
| 폴더선택 | 무관 | 항상 개별 |

### 탭 생성 규칙
| 모드 | 규칙 |
|------|------|
| 개별 (radio_indiv) | CycleGroup별 1탭 |
| 통합 (radio_overall) | file_idx별 1탭 |

### 연결 모드 개선
- 기존: `CycleMax[5]` 고정 배열 (최대 5채널)
- 변경: `channel_state` dict (채널 수 제한 없음)
