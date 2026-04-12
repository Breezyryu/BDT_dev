# 240323_pybamm_plot_axis_matching.md

---
**대상 함수/클래스**
- Electrode Balance plot ([1.2] subplot)
- 위치: DataTool_dev/DataTool_optRCD_proto_.py, pybamm_run_button() 내부

---
**처리 흐름**
1. 전체 OCP 커브: 0~1 stoichiometry 전체 구간에 대해 OCP 함수로 곡선 생성
2. 실사용 영역 OCP: 실제 시뮬레이션 결과의 stoichiometry 구간만 0~100%로 변환하여 곡선 생성
3. x축 변환식이 다르기 때문에 두 곡선이 완전히 겹치지 않음

---
**주요 파이썬 문법/패턴**
- np.linspace, np.asarray, ravel() 등 numpy 활용
- x축 변환: 100.0 * (pos_lith - _sto_p0) / _d_p
- 전체 OCP: _sto_full = np.linspace(0.001, 0.999, 500)

---
**Q&A 요약**
- Q: 전체 OCP와 실사용 OCP가 왜 정확히 매칭되지 않나?
- A: 전체 OCP는 0~1 전체 구간, 실사용 OCP는 실제 구간만 0~100%로 변환해서 x축 기준이 다름. 논문 스타일에서는 두 곡선을 구분해서 보여주는 것이 직관적임.

---
**영향 분석**
- x축 변환 기준이 다르므로, 두 곡선이 완전히 겹치지 않는 것이 정상 동작임.
- 필요시, x축 기준을 통일하는 방법도 구현 가능.

---
**관련 코드**
```python
# 전체 OCP 커브 (배경)
_sto_full = np.linspace(0.001, 0.999, 500)
_ocp_pos_full = np.asarray(_f_pos(_sto_full), dtype=float).ravel()
_soc_pe_full = 100.0 * (_sto_full - _sto_p0) / _d_p
ax.plot(_soc_pe_full, _ocp_pos_full, ...)

# 실사용 영역 OCP
_soc_sim = 100.0 * (pos_lith - _sto_p0) / _d_p
ax.plot(_soc_sim, pos_ocp, ...)
```

---
**작성일:** 2024-03-23
**작성자:** GitHub Copilot
