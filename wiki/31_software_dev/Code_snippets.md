---
title: "Code.i — LLM & 코딩 노트"
tags:
  - Development
  - 코드
  - LLM
  - AI
type: development
status: active
related:
  - "[[Python_환경설정]]"
  - "[[Summary_AI_Tech_Stack]]"
created: 2025-12-15
updated: 2026-03-17
source: "origin/Code.i.md"
---

## 언어 모델

언어 모델의 한계를 이해하면 높은 활용도를 구할 수 있을 것 같다.

![[Pasted image 20250416132248.png]]
### **대규모 언어 모델(Large Language Model)**
- 대규모 텍스트 데이터를 이용해 학습 (e.g. web pages, books, articles)
- 모델의 크기가 매우 큼
- 효율적인 학습을 위해 병렬 처리 기술을 사용
- 기존 언어 모델 대비 큰 모델과 대규모 데이터를 학습 함으로써 in-context learning을 수행할 수 있게 됨

## 언어 모델 구조 - Transformer
[Transformer 모델]
- 최신 언어 모텔 (LLM)에서 Transformer 모텔이 주로 사용됨
- Transformer는 자연어 처리 (NLP) 작업에 대한 성능 향상을 이루기 위한 아기텍처
[Transformer 모델의 특징]
- Self-attention 메커니즘을 활용한 문맥 파악
- 병렬 계산 가능한 구조로 효율적인 학습과 예측 가능
- 장거리 의존성을 효과적으로 모델링 할 수 있음

![[Pasted image 20250416132535.png]]
- 번역 모델을 사용하기 위해 Encoder와 Decoder를 같이 사용

Transformer 모델 유형
BERT (BidirectionaI Encoder Representations from Transformers)
- 양방향으로 문맥을 고려하여 단어를 인코딩
- 사전 훈련된 모델을 활용한 전이 학습에 매우 유용
GPT (Generative Pre-trained Transformer)
- 단방향으로 텍스트를 생성하는 모델
- 텍스트 생성, 완성, 번역 등에 활용

## 언어 모델 구조 - Tokenizer
- 자연어 처리에서 텍스트를 작은 단위로 분리하는 도구
- 텍스트를 언어 모델이 이해할 수 있는 단위로 분해하기 위해 사용
![[Pasted image 20250416132813.png]]
## Gauss Code 모델의 한계
 - Gauss Code모델은 Code 개발에 도움을 줄 수 있는 모델
 - 사람을 대신해 개발을 대신 해주는 모델은 아님
 - 학습하지 않은 내용을 생성하지 못할 수 있음
 - Hallucination이 발생할 수 있음
 - 이러한 한계를 이해하고 활용할 필요가 있음

## Prompt Engineering Techniques
- Chain of Thought
- Zero-shot CoT (Chain of Thought): Let's think step by step
- PoT(Pro)
