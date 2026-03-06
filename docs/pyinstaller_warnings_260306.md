# PyInstaller 빌드 Warning 분석 (2026.03.06)

## 빌드 결과

빌드 **정상 완료**. 아래 warning들은 전부 **무해**하며 exe 실행에 영향 없음.

---

## Warning 목록

### 1. casadi SyntaxWarning

```
casadi\tools\graph\graph.py:43: SyntaxWarning: invalid escape sequence '\<'
casadi\tools\graph\graph.py:43: SyntaxWarning: invalid escape sequence '\>'
```

- **원인**: casadi 소스코드에서 `\<`, `\>`를 raw string이 아닌 일반 string으로 사용 (casadi 코드 버그)
- **영향**: 없음. Python 3.12에서 경고만 발생, 동작에 문제 없음

### 2. scipy hidden import not found

```
WARNING: Hidden import "scipy.special._cdflib" not found!
```

- **원인**: scipy 최신 버전에서 `_cdflib` 모듈이 제거/변경됨
- **영향**: 없음. PyInstaller hook이 구버전 scipy 기준으로 작성되어 발생

### 3. casadi 상용/선택적 솔버 DLL 누락

| DLL | 솔버 | 종류 |
|-----|------|------|
| `libhsl.dll` | HSL 선형 솔버 | 상용 (학술 무료) |
| `knitro.dll` | KNITRO 비선형 최적화 | 상용 |
| `madnlp_c.dll` | MadNLP 솔버 | 선택적 |
| `snopt7.dll` | SNOPT 비선형 최적화 | 상용 |
| `worhp.dll` | WORHP 비선형 최적화 | 상용 |
| `libeng.dll` | MATLAB Engine | MATLAB 필요 |
| `libmx.dll` | MATLAB Matrix | MATLAB 필요 |

- **원인**: casadi가 지원하는 다양한 상용/선택적 솔버의 DLL. 설치하지 않으면 당연히 없음
- **영향**: 없음. PyBaMM은 기본 IPOPT 솔버를 사용하며, IPOPT는 이미 번들에 포함됨

---

## 결론

모든 warning은 무시 가능. exe 빌드 및 실행에 영향 없음.
