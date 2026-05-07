# onepath 빌드 — pandas._libs SubprocessDiedError 회피

- 작성일: 2026-05-07
- 대상: `build_exe_onepath.bat`

## 증상

```
PyInstaller.isolated._parent.SubprocessDiedError:
  Child process died calling _collect_submodules()
  with args=('pandas._libs', 'warn once') and kwargs={}.
  Its exit code was 3221225477
```

`exit code 3221225477` = `0xC0000005` = **STATUS_ACCESS_VIOLATION**
(Windows segfault). PyInstaller 가 pandas hook 처리 중 isolated
subprocess 를 띄워 `_collect_submodules('pandas._libs')` 호출.
그 subprocess 가 pandas binary extension 로드 시 access violation.

## 원인

PyInstaller 6.x 의 isolated subprocess 모드 — pandas/numpy 같이
binary extension 무거운 패키지의 hook 평가 시 child process 에서
DLL 의존성·메모리 충돌로 segfault 발생 빈번. 특히 pandas + numpy
+ matplotlib + 기타 native 모듈 조합에서 산발적.

## 해결

`--collect-all pandas` + `--collect-all numpy` 추가
([:54-58](../../build_exe_onepath.bat:54)).

```bat
--collect-all pybamm ^
--collect-all casadi ^
--collect-all pybammsolvers ^
--collect-all pandas ^      :: 신규 — _collect_submodules isolated subprocess 우회
--collect-all numpy ^       :: 신규 — 동일 패턴 예방
--hidden-import fsspec ^
```

`--collect-all` 은 PyInstaller 가 패키지 전체 (모듈·data·binary)
를 통째로 포함 — isolated subprocess 의 `_collect_submodules()`
호출 경로 자체를 우회하여 segfault 회피.

## 실패 시 추가 조치

위 변경으로도 동일 에러 발생 시:

1. **PyInstaller 업그레이드**
   ```cmd
   .venv\Scripts\pip install --upgrade pyinstaller
   ```

2. **pandas / numpy 재설치** (DLL 손상 가능성)
   ```cmd
   .venv\Scripts\pip install --force-reinstall --no-deps pandas numpy
   ```

3. **빌드 캐시 완전 초기화**
   ```cmd
   rmdir /s /q build dist __pycache__
   ```
   (bat 의 `--clean` 외에 `build/` 폴더도 수동 삭제)

4. **PyInstaller isolation 비활성화** (최후 수단, 6.x 전용 옵션 확인 필요)
   - 환경변수 `PYINSTALLER_DISABLE_ISOLATION=1` 또는
   - `pyinstaller --no-isolated ...` (버전에 따라 가능)

## 트레이드오프

- 빌드 시간 약간 증가 (collect-all 로 추가 파일 포함)
- 출력 폴더 크기 증가 (pandas/numpy 의 unused 모듈도 포함)
- 안정성 우선 — segfault 회피가 가장 큰 이득
