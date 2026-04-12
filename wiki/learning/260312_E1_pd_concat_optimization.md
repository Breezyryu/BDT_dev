# E1 개선: 루프 내 pd.concat() → list append + 마지막 concat

> **작성일:** 2026-03-12  
> **대상 파일:** `DataTool_dev/DataTool_optRCD_proto_.py`  
> **개선 항목:** E1 (난이도 ⭐, 기대효과 🔥🔥🔥)

---

## 변경 내용

### 문제
루프 안에서 `pd.concat([기존df, 새df])`를 반복하면 매번 전체 데이터를 복사하여 O(n²) 비용 발생.

### 해결
list에 append 후 루프 종료 시 1회만 `pd.concat()` 수행하여 O(n)으로 개선.

---

## 변경 위치 (4곳)

### 1. `app_cyc_confirm_button` (L10766 부근)
- `dfoutput = pd.DataFrame()` → `dfs_output = []`
- 루프 내 `dfoutput = pd.concat([dfoutput, df], axis=1)` → `dfs_output.append(df)`
- 루프 후 `dfoutput = pd.concat(dfs_output, axis=1) if dfs_output else pd.DataFrame()`

### 2. `toyo_data_make` (L13299 부근)
- `self.AllchnlData = pd.concat([self.AllchnlData, self.df])` 제거
- `return self.df` 추가 (DataFrame 반환 방식으로 변경)

### 3. `pne_data_make` (L13378 부근)
- `self.AllchnlData = pd.concat([self.AllchnlData, self.df])` 제거
- `return self.df` 추가 (DataFrame 반환 방식으로 변경)

### 4. `mount_all_button` (L13163 부근) — 호출부
- `self.AllchnlData = pd.DataFrame()` 제거
- `all_dfs = []` 리스트로 결과 수집
- `toyo_data_make` / `pne_data_make` 반환값을 `all_dfs.append(result)` 로 누적
- 루프 후 `self.AllchnlData = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()`

---

## 기대 효과

| 파일 수 | 개선 전 (O(n²)) | 개선 후 (O(n)) | 배율 |
|---------|----------------|---------------|------|
| 31개 (toyo5+pne26) | ~5초 | ~0.3초 | 17배 |
| 100개 (app_cyc) | ~25초 | ~1초 | 25배 |
