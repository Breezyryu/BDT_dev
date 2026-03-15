---
tags: [AI, summary, knowledge_base, python, pytorch]
up: [[Simulation & Modeling]]
status: stable
created: 2026-01-27
aliase: [AI Concept Summary]
---

# AI & Deep Learning Tech Stack Summary

## 1. Core Frameworks

### 1.1 Python & PyTorch

- **Python**: Dynamic typing, strong ecosystem (List, Tuple, Dict).
- **PyTorch**:
  - **Tensor**: 다차원 배열, GPU 가속(`.to("cuda")`), 자동 미분(Autograd) 지원.
  - **Module**: `nn.Module` 상속으로 커스텀 신경망 정의 (`__init__`, `forward`).
  - **DataLoader**: 배치(Batch) 단위 데이터 처리 및 셔플링.

### 1.2 Comparison

- **TensorFlow**: Google 개발. 대규모 배포/운영(Production)에 유리.
- **PyTorch**: Meta 개발. 연구/실험(Research) 및 디버깅 용이.

## 2. Deep Learning Fundamentals

![[2025-05-26 NN(Nueral Network).excalidraw|600]]
> *그림 1: 신경망(Neural Network)의 기본 구조 및 학습 흐름*

### 2.1 Training Pipeline

1. **Forward**: 입력 $\to$ 모델 $\to$ 예측값 산출.
2. **Loss Calculation**: 예측값 vs 실측값 오차 계산 (MSE, Cross-Entropy).
3. **Backward (Backprop)**: `loss.backward()`로 기울기(Gradient) 계산.
4. **Optimization**: `optimizer.step()`으로 가중치 업데이트 (Adam, SGD).

### 2.2 Activation Functions

- **Sigmoid/Tanh**: 기울기 소실(Vanishing Gradient) 문제 존재.
- **ReLU**: 음수=0, 양수=그대로. 가장 보편적.
- **Leaky ReLU**: 음수 영역에 작은 기울기 부여 (Dying ReLU 방지).

## 3. Key Architectures

### 3.1 CNN (Image Processing)

- **Structure**: Conv(특징 추출) $\to$ Pooling(압축) $\to$ FC(분류).
- **History**:
  - **AlexNet(2012)**: GPU 활용, ReLU 도입.
  - **ResNet(2015)**: Skip Connection으로 깊은 망 학습 가능 ($y = F(x) + x$).
  - **ViT(2020)**: Transformer를 이미지에 적용 (Patch 단위 처리).

### 3.2 RNN & NLP (Sequence Processing)

- **RNN**: 이전 상태(Hidden state)를 현재 입력과 함께 처리.
- **LSTM/GRU**: 게이트(Gate) 구조로 장기 의존성(Long-term dependency) 해결.
- **Attention/Transformer**: 병렬 처리 가능, 대규모 언어 모델(LLM)의 기반.

## 4. Generative Models

### 4.1 Image Generation

- **GAN**: Generator(생성) vs Discriminator(판별) 적대적 학습.
- **VAE**: 잠재 공간(Latent space)의 확률 분포 학습.
- **Diffusion**: 노이즈 추가(Forward) $\to$ 제거(Reverse) 과정을 학습 (Stable Diffusion).

### 4.2 Application

- **Semantic Segmentation**: 픽셀 단위 분류 (UNet).
- **Object Detection**: 위치(B-Box) + 분류 (YOLO, R-CNN).

## 📚 관련 노트 (Related Notes)
- **심화 학습 (Deep Dive)**: [[Knowledge_PINN_DeepONet]] (Physics-Informed Neural Networks 심화)
- **활용 사례**: [[Empirical_Degradation_Models]] (데이터 기반 모델링과의 비교)
- **상위 개념**: [[모델링 및 AI (Modeling & AI)]]

