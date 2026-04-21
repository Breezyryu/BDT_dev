# UI Improvement Log: DataTool_optRCD_proto_.py

**Date:** 2026-03-19  
**Target Group:** Mobile Li-ion Battery Development Group  
**Reference:** `frontend-design.instructions.md` (PyQt6 Frontend Design Skill)

---

## 1차 수정 (16:16)
- 원본 보호를 위해 `DataTool_optRCD_proto_UI.py` 복사본 생성
- `apply_ui_theme.py` 스크립트로 글꼴/색상 일괄 교체

## 2차 수정 (16:20) — `frontend-design.instructions.md` 기준

### Fonts (2 Fonts)
| 용도 | Font | 적용 범위 |
|------|------|-----------|
| Main UI | `Segoe UI` | QMainWindow 전역 QSS, matplotlib rcParams |
| Data/Mono | `Consolas` | QLineEdit, QTextEdit, QPlainTextEdit |

### Colors (3 Base Hues + Tonal Gradations)
| 기본 색상 | Hex | 파생 톤 |
|-----------|-----|---------|
| **Navy** (Accent) | `#2b5c8f` | primary, accent, ring, selected tab |
| **White** (Background) | `#FFFFFF` | bg → #FAFAFA → #F5F5F5 → #F0F0F0 |
| **Charcoal** (Text) | `#333333` | fg → #666666 → #888888 → #999999 → #C0C0C0 |

### Key Fixes (2차)
1. **Border 색상**: `#333333` → `#C0C0C0` (너무 어두웠던 테두리를 연한 회색으로 수정)
2. **Graph PALETTE 복원**: 3색 → 원래 10색 복원 (다채널 배터리 데이터 시각화에 필수)
3. **Grid/Spine 색상 개선**: `#666666` → `#E0E0E0` / `#999999` (그래프 가독성 향상)
4. **Tab 호버**: border 색상 대신 `zinc200 (#E4E4E4)`로 부드러운 피드백
5. **QSS font-family**: QMainWindow에 `font-family: "Segoe UI"` 명시적 선언
6. **muted_fg**: `#333333` → `#888888` (부가 텍스트 구분 강화)

### Agent Skills Used
- `frontend-design.instructions.md` (PyQt6 Frontend Design Skill)
- `run_command` (PowerShell file duplication)
- `sequential-thinking` MCP server (디자인 의사결정 분석)
