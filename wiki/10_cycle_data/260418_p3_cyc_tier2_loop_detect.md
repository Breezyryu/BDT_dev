# P3: `.cyc` 단독 Tier 2 구현 — LOOP 감지 + 한계 분석

**날짜**: 2026-04-18  
**관련 브랜치**: `claude/agitated-liskov-6c436a`

## 배경

P2b에서 발견한 "StepType=8 → TC++" 규칙이 SaveEndData col[2] 기반으론 99.98% 정확.
자정 전 데이터(Restore/SaveEndData 미생성)에서도 이 규칙을 적용하려면 `.cyc` 레코드에서 **LOOP 마커를 정확히 감지**해야 함.

## 변경 내용

### 신규 파일
- `DataTool_dev_code/tools/cyc_reader.py`: 독립적 PNE `.cyc` 바이너리 파서
  - `parse_cyc_header()`: 헤더 + FID 목록 파싱
  - `read_cyc_records()`: seek+read로 레코드 영역 로드 (float32)
  - `detect_loop_markers()`: LOOP 마커 감지
  - `extract_step_sequence()`: (RecIdx, inferred_StepType) 시퀀스 추출
- `DataTool_dev_code/tools/tier2_validate.py`: Tier 2 end-to-end 검증 스크립트

### 수정
- `tc_rebuilder.py`: `load_from_cyc()` + `build_channel_tc()` Tier 2 활성화

## LOOP 감지 규칙

**signature**: 스텝의 마지막 레코드에서 StepTime 점프 > 300초

```python
def detect_loop_markers(records, hdr, jump_threshold=300.0):
    step_t = hdr.fid_pos[FID_STEP_TIME]
    times = records[:, step_t]
    starts = np.where(times == 0.0)[0].tolist() + [len(records)]
    loops = []
    for i in range(len(starts) - 1):
        s, e = starts[i], starts[i + 1] - 1
        if e > s and times[e] - times[e - 1] > jump_threshold:
            loops.append(e)
    return loops
```

**근거**: PNE 장비가 LOOP 완료를 스텝 마지막 레코드에 기록하며 해당 레코드의 StepTime이 Loop 전체 누적 시간 (수천~수만 초)으로 저장. 일반 휴지 스텝 내부 레코드 간격(≤수분) 대비 압도적.

## 검증 결과

### Layer 1: LOOP 감지 정확도 (15 채널)
- **Precision**: 98.67% (445/451)
- **Recall**: 98.89% (445/450)

### Layer 2: Tier 2 end-to-end (20 채널, SaveEndData를 ground truth로)
- 완벽(100%): 13/20 채널
- 부분(≥12%): 7/20 채널 — LOOP 1개 누락 시 이후 TC 연쇄 오프셋
- **총 정확도**: 45.73% (2105/4603)

### 한계: 누적 오차 전파

**증상**: LOOP 38개 중 1개를 놓치면 해당 시점 이후 모든 TC가 `-1`로 어긋남 → 7% 수준의 연쇄 실패

**사례**:
- `260223/Q8main ATL GEN5+B`: 공통 366행 중 일치 26행 (7.1%)
- 원인: 특정 시점에 짧은 Loop(<300s 점프)를 `cond_a`로 감지 실패

## 한계 해결 방향 (P4+)

### 옵션 A: Recall 100% (이상적)
- 짧은 Loop도 감지하는 추가 signature 필요 — DchgCap/ChgCap 급변, 다음 레코드의 Current 방향 반전 등 보조 조건
- jump_threshold를 동적으로 (중앙값 기반)

### 옵션 B: 하이브리드 체크포인트 (실용적, 권장)
- SaveEndData가 **일부라도 있으면** 그 범위까지는 Tier 1
- 자정 전 tail은 `.cyc`의 **마지막 SaveEndData RecIdx 이후**만 재구성
- 체크포인트 TC로 리셋되므로 누적 오차 감쇠
- 기존 `c68aae4` 커밋의 "보충" 모드와 철학 일치

### 옵션 C: 독립 TC 추론 (근본적)
- 각 TC 경계를 **전역 relative position**으로 계산 (누적 아닌)
- `.sch` 예상 그룹 구조와 매칭해서 offset 자동 보정
- 구현 복잡, but 체크포인트 없이도 작동

## 결정

**현재 상태에서 가장 실용적**: 옵션 B 하이브리드
- 자정 이후 정기 시점에 SaveEndData 생성 → Tier 1로 큰 오차 리셋
- 자정 전 새 레코드는 짧은 구간이라 누적 오차 ≤ 몇 %
- 기존 c68aae4의 `_cached_pne_restore_files` 보충 로직이 이미 이 방향

## 다음 단계

- **P4: 기존 API 교체**
  - `get_cycle_map` → `tc_rebuilder.build_channel_tc()` 라우팅
  - `_cyc_to_cycle_df`의 heuristic TC 로직을 cyc_reader.detect_loop_markers + 체크포인트로 교체
  - 하이브리드 체크포인트 구현 (옵션 B)
- **P5: 휴리스틱 정리 + `.sch` 카테고리 라벨**
  - profile 분석 UI에 카테고리 필터 노출

## 참고

- 커밋 히스토리: `3a69aed` (P1), `c6299b6` (P2 failed), `53feda1` (P2b schema)
- 이번 작업 관련 파일:
  - `tools/cyc_reader.py`: 독립 파서
  - `tools/tc_rebuilder.py`: Tier 2 활성화
  - `tools/tier2_validate.py`: E2E 검증 스크립트
