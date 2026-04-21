---
relocated: 2026-04-22
source_vault: "docs/vault/01_Modeling_AI/phygnn_NREL.md"
title: "phygnn (Physics-Guided NN, NREL)"
aliases:
  - phygnn
  - Physics-Guided Neural Network
tags:
  - Modeling_AI
  - PINN
  - NREL
  - reference
  - library
type: reference
status: active
related:
  - "[[NREL_PINN]]"
  - "[[PINN_기초]]"
  - "[[PINN_문헌정리]]"
  - "[[Knowledge_PINN_DeepONet]]"
  - "[[Summary_AI_Tech_Stack]]"
created: 2026-04-19
updated: 2026-04-19
source: "https://github.com/NatLabRockies/phygnn"
---

# phygnn (Physics-Guided Neural Networks)

> [!abstract] 요약
> NREL(국립재생에너지연구소)에서 개발한 **Physics-Guided Neural Network** 프레임워크.
> 표준 데이터 손실에 **물리 제약 손실항(`p_fun`)** 을 가중 결합하여,
> NN 출력이 데이터를 맞추면서도 물리적으로 일관되도록 학습시키는 TensorFlow 2.x 기반 라이브러리.

- 저장소: https://github.com/NatLabRockies/phygnn
- 라이선스: BSD-3 (NREL)
- 분석일: 2026-04-19

---

## 1. 핵심 개념

### 이중 손실(Dual-Loss) 구조

$$
\mathcal{L}_{\text{total}} = w_1 \cdot \mathcal{L}_{\text{data}}(\hat{y}, y) + w_2 \cdot \mathcal{L}_{\text{phys}}(\text{p\_fun}) + \mathcal{L}_{\text{reg}}
$$

- `L_data`: 일반적 MSE / CrossEntropy
- `L_phys`: 사용자 정의 물리 함수 `p_fun` 출력(반드시 **미분가능**)
- `L_reg`: kernel/bias 정규화 (L1/L2 선택)
- 기본 `loss_weights = (0.5, 0.5)`

### `p_fun` 시그니처
```python
p_fun(model: PhysicsGuidedNeuralNetwork,
      y_pred: tf.Tensor,
      X: np.ndarray,
      extra: np.ndarray) -> tf.Tensor  # scalar loss
```
- NN 예측을 물리 모델에 투입 → 물리 모델 출력과 관측치를 비교
- 예: NREL의 위성 구름광학 → 전자기파 복사전달 모델 → 지표 일사량 비교

---

## 2. 패키지 구조

```
phygnn/
├── __init__.py
├── base.py               # 네트워크 골격, 레이어 빌더
├── phygnn.py             # PhysicsGuidedNeuralNetwork 코어 클래스
├── layers/               # 커스텀 레이어
├── model_interfaces/
│   ├── base_model.py     # 모델 추상 베이스
│   ├── phygnn_model.py   # phygnn 전용 인터페이스
│   └── tf_model.py       # 순수 TF 모델 래퍼
└── utilities/            # 보조 유틸
```

### 예제 노트북
| 파일 | 내용 |
|---|---|
| `phygnn_pythag.ipynb` | 피타고라스 정리($a^2+b^2=c^2$)를 물리 제약으로 부과하는 토이 예제 |
| `phygnn_classification.ipynb` | 분류 문제에 물리 제약 적용 |
| `phygnn_nsrdb_gan.ipynb` | 태양복사량(NSRDB) 데이터 기반 물리제약 GAN |

---

## 3. 주요 API (요약)

### 초기화
```python
from phygnn import PhysicsGuidedNeuralNetwork

model = PhysicsGuidedNeuralNetwork(
    p_fun=my_physics_loss,      # 핵심: 물리 함수
    loss_weights=(0.5, 0.5),    # (data, physics)
    hidden_layers=[{'units': 64, 'activation': 'relu'}, ...],
    input_layer=True,
    output_layer=True,
    metric='mae',
    learning_rate=1e-3,
    kernel_reg_rate=0.0,
    kernel_reg_power=1,         # 1=L1, 2=L2
)
```

### 학습
```python
history = model.fit(
    x=X_train, y=y_train,
    p_kwargs={...},         # p_fun에 전달할 부가 인자
    n_batch=16,
    n_epoch=100,
    validation_split=0.2,
)
```

### 저장/로드
- `model.model_params` → 하이퍼파라미터 + 히스토리 dict
- pickle 기반 직렬화 (TF weights + params)

---

## 4. BDT 관점 — 참고 포인트

> [!tip] 배터리 도메인 응용 가능성
> phygnn의 **`p_fun` 패턴**은 배터리 NN 모델 전반에 이식 가치가 높음.

### (a) SOC/SOH 추정 NN → 쿨롱 카운팅 제약
$$
\mathcal{L}_{\text{phys}} = \left\| \hat{Q}(t) - \hat{Q}(0) - \int_0^t \hat{\eta}\, I(\tau)\, d\tau \right\|^2
$$
- NN이 예측한 용량 변화와 실제 전류 적분값의 정합을 손실로 부과
- BDT의 `ChgCap`/`DchgCap` 컬럼을 실시간 제약에 활용 가능

### (b) 열화 예측 — PyBaMM 연동
- 직접 연결은 **미분가능성 이슈**로 어려움
- **Surrogate(다항식·GP·작은 NN)** 로 pybamm SPM을 근사 → `p_fun`으로 투입
- 관련: [[PyBaMM_정리]], [[PyBaMM_Solve]], [[PINN_기초]]

### (c) dV/dQ 피크 위치 추정
- 음극/양극 밸런스 물리식([[Empirical_Degradation_Models]] 참조)을 제약으로
- 노이즈 많은 실측 dV/dQ에서 피크 검출 강건성 향상 기대

### (d) 손실 가중치 스케줄링
- 초기: `w_phys` 크게 → 물리적으로 타당한 영역으로 가이드
- 후기: `w_data` 증가 → 실측 데이터에 핏
- 소량·고노이즈 배터리 데이터에 특히 유용

### (e) 모델 직렬화 패턴
- `model_params` (하이퍼파라미터 + 학습 히스토리 DataFrame) 묶음 저장
- BDT 장기 사이클 데이터 기반 모델에 그대로 이식 가능

---

## 5. 한계 및 도입 시 고려사항

| 항목 | 이슈 | 대응 |
|---|---|---|
| **프레임워크** | TensorFlow 2.x 전용 | BDT가 PyTorch 중심이면 "아이디어 이식" 권장 |
| **미분가능성** | pybamm 같은 ODE 솔버 직결 불가 | Surrogate 모델 필요 |
| **예제 도메인** | 태양광(NSRDB) 중심 | 배터리 사례 직접 포팅 |
| **학습 비용** | 이중 손실로 수렴 느릴 수 있음 | 가중치 스케줄링, pretrain |
| **`p_fun` 사전검사** | TF 그래프에서 gradient 생성 가능 여부 자동 체크 | 설계 초기에 검증 |

---

## 6. 결론

- **프레임워크 자체 도입**: 스택 불일치(TF) + pybamm 미분 이슈로 부담 큼
- **차용할 가치**:
  1. `p_fun` 패턴 (물리 함수를 손실항으로 삽입)
  2. 이중 손실 가중치 구조 + 스케줄링
  3. 미분가능성 사전검사
  4. `model_params` 직렬화 컨벤션
- 동일 패턴의 **PyTorch 구현**은 자체 작성이 현실적
  ([[PINN_기초]], [[Summary_AI_Tech_Stack]] 참고)

---

## 7. 참고 링크

- GitHub: https://github.com/NatLabRockies/phygnn
- NREL 논문 (관련): https://arxiv.org/pdf/2312.17329
- 관련 개념: [[PINN_기초]], [[PINN_문헌정리]], [[NREL_PINN]]

## 관련 노트

- [[NREL_PINN]] — NREL의 PINN 연구 동향 (배터리 쪽)
- [[PINN_기초]] — Physics-Informed NN 기본
- [[Knowledge_PINN_DeepONet]] — PINN/DeepONet 심화
- [[PyBaMM_정리]] — 물리 모델 연동 시 surrogate 대상
- [[Summary_AI_Tech_Stack]] — PyTorch 이식 고려 시
