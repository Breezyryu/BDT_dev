---
title: "Cuda 설정 (25년 8월 기준)"
tags:
  - Development
  - CUDA
  - GPU
  - 환경설정
type: development
status: active
related:
  - "[[Python_환경설정]]"
  - "[[Summary_AI_Tech_Stack]]"
created: 2025-12-15
updated: 2026-03-17
source: "origin/Cuda 설정 (25년 8월 기준).md"
---

# 1. [CUDA GPU Compute Capability | NVIDIA Developer](https://developer.nvidia.com/cuda-gpus)
- local GPU: NVIDIA RTX A4000 / Compute Capability: **8.6**

# 2. Coumpute Capa에 맞는 CUDA 버전 확인
[CUDA - Wikipedia](https://en.wikipedia.org/wiki/CUDA#GPUs_supported)
[Support Matrix — NVIDIA cuDNN Backend](https://docs.nvidia.com/deeplearning/cudnn/backend/latest/reference/support-matrix.html)
[[Pasted image 20250822075917.png]]
- 8.6 기준으로  CUDA SKD version 11.1 ~ 13.0 이용 가능
- ![[Pasted image 20250822080635.png]]
# 3. Pytorch 지원 CUDA 버전
![[Pasted image 20250822080113.png]]
- CUDA 12.9까지 지원 / 13.0은 미지원

# 4. 설치된 cuda 버전 확인
- cmd 창에서 입력
- 'nvcc -ver' 또는 'nvcc -V' : CUDA-toolkit 에 의해 결정 / runtime API version
- 'nvidia-smi' : GPU driver installer에 결정 / driver API version
- nvcc -ver < nvidia-smi 이면 그냥 써도 무방

# 5. 참고사항
- CUDA는 abstract된 라이브러리로 자세한 기술문서는 아래 링크 참고
- [CUDA Toolkit Documentation 13.0](https://docs.nvidia.com/cuda/)
