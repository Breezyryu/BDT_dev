"""cyc_reader.py — 독립적인 PNE .cyc 바이너리 파서.

포맷 (260410_study_pne_cyc_vs_csv_structure.md 기반):
    0x000–0x147 : 메타 (328B)
    0x148       : n_fields (uint32 LE)
    0x14C       : FieldID 배열 (uint16 LE × n_fields)
    0x1B0       : 데이터 시작 — float32 × n_fields × N_records

레코드 크기 = n_fields × 4 bytes.
"""
from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from typing import Optional

import numpy as np

# ---------- 상수 ----------
META_END = 0x148            # n_fields 위치
FID_TABLE_START = 0x14C
DATA_START = 0x1B0          # float32 레코드 시작 (고정 추정)

# 주요 FID 코드 (메모리 pne_data_characteristics 참조)
FID_VOLTAGE = 1             # mV
FID_CURRENT = 2             # mA
FID_STEP_TIME = 6           # sec (스텝 시작 = 0)
FID_TOTAL_TIME = 7          # sec (누적, LOOP 마커에서 불변 추정)
FID_TEMP1 = 12              # °C
FID_INDEX = 22              # 레코드 번호
FID_AVG_VOLTAGE = 24        # mV
FID_CHG_CAP = 26            # mAh
FID_DCHG_CAP = 27           # mAh
FID_DCHG_ENG = 35           # Wh
FID_DATE = 43               # YYMMDD
FID_TIME = 44               # HHMMSSmmm
FID_V_MAX = 45              # uV
FID_TEMP4 = 49              # °C or m°C


@dataclass
class CycHeader:
    """파싱된 .cyc 헤더."""

    path: str
    n_fields: int
    fids: list[int]              # FID 리스트 (레코드 내 순서)
    fid_pos: dict[int, int]      # FID → 레코드 내 컬럼 인덱스
    rec_size: int                # 바이트
    data_start: int              # 바이트 오프셋
    file_size: int
    n_records: int               # (file_size - data_start) / rec_size


def parse_cyc_header(path: str) -> Optional[CycHeader]:
    """`.cyc` 파일 헤더 파싱."""
    try:
        file_size = os.path.getsize(path)
        if file_size < DATA_START:
            return None
        with open(path, "rb") as f:
            hdr = f.read(DATA_START)
    except OSError:
        return None

    n_fields = struct.unpack_from("<I", hdr, META_END)[0]
    if n_fields <= 0 or n_fields > 200:
        return None

    fids: list[int] = []
    for i in range(n_fields):
        off = FID_TABLE_START + i * 2
        if off + 2 > len(hdr):
            return None
        fid = struct.unpack_from("<H", hdr, off)[0]
        fids.append(fid)

    fid_pos = {fid: i for i, fid in enumerate(fids)}
    rec_size = n_fields * 4
    data_bytes = file_size - DATA_START
    n_records = data_bytes // rec_size

    return CycHeader(
        path=path,
        n_fields=n_fields,
        fids=fids,
        fid_pos=fid_pos,
        rec_size=rec_size,
        data_start=DATA_START,
        file_size=file_size,
        n_records=n_records,
    )


def read_cyc_records(
    hdr: CycHeader,
    start_idx: int = 0,
    count: Optional[int] = None,
) -> np.ndarray:
    """`.cyc` 레코드 배열을 로드 (float32, shape (N, n_fields)).

    start_idx, count는 0-based 레코드 인덱스.
    """
    if start_idx < 0:
        start_idx = 0
    if count is None or count < 0:
        count = max(0, hdr.n_records - start_idx)
    count = min(count, max(0, hdr.n_records - start_idx))
    if count == 0:
        return np.empty((0, hdr.n_fields), dtype=np.float32)

    byte_offset = hdr.data_start + start_idx * hdr.rec_size
    byte_count = count * hdr.rec_size

    with open(hdr.path, "rb") as f:
        f.seek(byte_offset)
        raw = f.read(byte_count)

    arr = np.frombuffer(raw, dtype="<f4").reshape(-1, hdr.n_fields)
    return arr


def find_record_by_index(
    hdr: CycHeader, records: np.ndarray, target_idx: int
) -> Optional[np.ndarray]:
    """records 배열에서 FID 22(Index) == target_idx 인 행 반환."""
    pos = hdr.fid_pos.get(FID_INDEX)
    if pos is None:
        return None
    mask = records[:, pos].astype(np.int64) == target_idx
    found = np.where(mask)[0]
    if len(found) == 0:
        return None
    return records[found[0]]


def find_step_boundaries(records: np.ndarray, step_time_pos: int) -> list[int]:
    """StepTime == 0 위치를 스텝 경계로 반환 (record 인덱스)."""
    return np.where(records[:, step_time_pos] == 0.0)[0].tolist()


def detect_loop_markers(
    records: np.ndarray,
    hdr: CycHeader,
    jump_threshold: float = 300.0,
) -> list[int]:
    """스텝 마지막 레코드의 StepTime 점프로 LOOP 마커 감지.

    PNE 장비는 LOOP 완료를 스텝 마지막 레코드에 기록하며, 이 레코드의
    StepTime은 해당 Loop 전체의 누적 시간 같은 큰 값 (수천~수만 초)으로
    저장됨. 일반 충방전/휴지 스텝 내부 연속 레코드의 StepTime 간격(<=수분)
    과 비교해 압도적으로 큼.

    실측 검증 (15 채널): Precision 98.67%, Recall 98.89%

    Parameters
    ----------
    records : np.ndarray
        (N, n_fields) float32 레코드 배열.
    hdr : CycHeader
    jump_threshold : float
        스텝 마지막 ↔ 직전 레코드 StepTime 점프 임계값 (초). 기본 300.

    Returns
    -------
    list[int]
        LOOP 마커로 감지된 레코드 인덱스 (records 내 0-based).
    """
    step_t = hdr.fid_pos.get(FID_STEP_TIME)
    if step_t is None or len(records) == 0:
        return []

    times = records[:, step_t]
    N = len(records)

    # 스텝 시작점 + 가드
    starts = np.where(times == 0.0)[0].tolist() + [N]

    loops: list[int] = []
    for i in range(len(starts) - 1):
        s = int(starts[i])
        e = int(starts[i + 1]) - 1
        if e <= s:
            continue
        last_t = float(times[e])
        prev_t = float(times[e - 1])
        if last_t - prev_t > jump_threshold:
            loops.append(e)
    return loops


def extract_step_sequence(
    records: np.ndarray,
    hdr: CycHeader,
    loop_threshold: float = 300.0,
) -> list[tuple[int, int]]:
    """.cyc 레코드에서 (Index, inferred_StepType) 시퀀스 추출.

    inferred_StepType은 SaveEndData col[2] StepType 코드와 호환:
        1 = 충전 (평균 전류 > 10 mA)
        2 = 방전 (평균 전류 < -10 mA)
        3 = 휴지 (그 외)
        8 = LOOP (detect_loop_markers)

    각 스텝의 마지막 레코드 하나만 반환 — SaveEndData의 스텝-종료 기록과 동일 형태.
    """
    idx_col = hdr.fid_pos.get(FID_INDEX)
    step_t = hdr.fid_pos.get(FID_STEP_TIME)
    curr = hdr.fid_pos.get(FID_CURRENT)
    if idx_col is None or step_t is None or curr is None:
        return []

    times = records[:, step_t]
    currents = records[:, curr]
    N = len(records)
    starts = np.where(times == 0.0)[0].tolist() + [N]

    loop_set = set(detect_loop_markers(records, hdr, loop_threshold))

    out: list[tuple[int, int]] = []
    for i in range(len(starts) - 1):
        s = int(starts[i])
        e = int(starts[i + 1]) - 1
        if e < s:
            continue
        end_rec_idx = int(records[e, idx_col])

        if e in loop_set:
            stype = 8
        else:
            mean_i = float(np.mean(currents[s:e + 1])) if e >= s else 0.0
            if mean_i > 10.0:
                stype = 1
            elif mean_i < -10.0:
                stype = 2
            else:
                stype = 3
        out.append((end_rec_idx, stype))
    return out


# ---------- CLI ----------
if __name__ == "__main__":
    import sys

    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("Usage: cyc_reader.py <cyc_path>")
        sys.exit(1)

    hdr = parse_cyc_header(sys.argv[1])
    if hdr is None:
        print("Parse failed")
        sys.exit(1)

    print(f"=== {os.path.basename(hdr.path)} ===")
    print(f"n_fields : {hdr.n_fields}")
    print(f"rec_size : {hdr.rec_size} bytes")
    print(f"n_records: {hdr.n_records}")
    print(f"FIDs     : {hdr.fids}")
    print()
    # 처음 3 레코드 샘플
    recs = read_cyc_records(hdr, 0, 3)
    print("첫 3 레코드 (주요 FID만):")
    for i, rec in enumerate(recs):
        row = {
            f"FID{fid}": float(rec[hdr.fid_pos[fid]])
            for fid in (FID_INDEX, FID_STEP_TIME, FID_TOTAL_TIME, FID_VOLTAGE,
                        FID_CURRENT, FID_DCHG_CAP, FID_DATE, FID_TIME)
            if fid in hdr.fid_pos
        }
        print(f"  rec {i}: {row}")
