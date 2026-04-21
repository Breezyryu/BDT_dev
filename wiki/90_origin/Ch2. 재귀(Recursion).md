---
title: Ch2. 재귀(Recursion)
category: Resource/Code
created: 2025-12-15
tags:
  - reference
---

# function recursion
## 1. Fuction: stack & heap flow
 ![[Pasted image 20251119122625.png]]
 [[Pasted image 20251119122638.png]]
## 2. 재귀 호출
![[Pasted image 20251119123312.png]]
	- 함수들이 쌓이고 return 값이 0, 1, 2, 3, 4, 5 순서로 cout
## 3. 재귀로 합 
![[Pasted image 20251119125103.png]]
	- 일반 합: n의 크기에 상관없이, sum, i 의 공간복잡도 O(1)
	- 재귀 : stack에 누적되므로 공간복잡도 O(n)
		- ![[Pasted image 20251119125313.png]]
		- 오히려, 재귀(=함수 호출)가 메모리를 더 쓴다.
		- 시간(연산) 복잡도는 둘 다 O(n)
## 4. Fibonnacci
- 재귀적![[Pasted image 20251119134914.png]]
## 5. 재귀 이진 탐색
- ![[Pasted image 20251119144430.png]]
- 범위를 반씩 나눠가며 재귀함수 호출
## 6. 순열(permutation)
- ![[Pasted image 20251119145709.png]]
- 
 