---
title: ECT
category: Project/Battery_Research
created: 2025-12-15
tags:
  - battery
  - research
status: active
updated: 2025-12-15
---

# 정리
- Roadmap
	![[Pasted image 20251212095012.png]]
	![[Pasted image 20251212095046.png]]
	![[Pasted image 20251212095133.png]]
	![[Pasted image 20251212095638.png]]
	
## 알고리듬
- UI
								![[Pasted image 20251212095306.png]]
- figure
		![[Pasted image 20251212093334.png]]
		![[Pasted image 20251212093659.png]]
		![[Pasted image 20251212093734.png]]
- 
	
Code size = 15KB
![[Pasted image 20251212085841.png]]
![[Pasted image 20251212085826.png]]
- 열화정보
	![[Pasted image 20251212090007.png]]
- Parameter 정의
![[Pasted image 20251212090127.png]]
- 음극 half코인셀 GITT OCP 기반으로 양극 OCP 추출
- 셀 EIS 측정 > ECM모델로 양음극 저항 산정 > 음극SEI 저항, 반응속도상수 도출
- LUT
	LDP Adaptive Charge
	![[Pasted image 20251212085434.png]]
	- 실시간 운전data기반 전기화학모델 열화파라미터update → C-rate별 부반응 전류 계산  → 음극전위 변화에 따른 충전 효율 계산 → 최적 LUT 도출 : 충전경로에 따른 열화량 비교, 최소 열화량 충전 경로 도출
- 내부단락
	- ![[Pasted image 20251212090749.png]]
	- 전기화학 모델과 배터리 응답 특성 비교 à 실운전 조건에서 단락 저항(≤ 500Ω) 진단 알고리듬 확보
- 열화 Parameter
	- 변수 스크리닝
		![[Pasted image 20251212090952.png]]
		1. 전체변수 400개
			- Scalar
				- 셀 형상
				- 물성
				- 열화 변수 (문헌, 선행 지식 기반 스크리닝)
			- Vector
				- 활물질 diffusivity
		2. 1차 스크리닝 : 문헌, 선행 지식 기반 열화 관련 변수
			- 양음극 활물질 부피 분율 : 감소 방향
			- 양음극, 분리막 전해질 부피 분율 : 감소 방향
			- 양음극 SEI 피막 저항 : 감소 방향
			- 양음극 ocp balance shift
			- 전해질 농도 : 감소 
		3. 2차 스크리닝 : 민감도, 경향성 분석
			- 양음극 활물질 부피 분율
			- 음극 SEI 저항
			- 양음극 balance shift
		4. 3차 스크리닝: dV/dSOC plot
			- SOH 구간 별 dV/dSOC plot으로 graphite peak shift
			- 유효 변수 도출
	- 열화 변수
		1. 음극 SEI 저항 증가 추정
			- profile dV 기준 산정
				![[Pasted image 20251212092248.png]]
		2. 양극 활물질 용량 감소 추정
				![[Pasted image 20251212092343.png]]
		3. 양음극 밸런싱 변화 추정
				![[Pasted image 20251212092401.png]]
			
- 급속충전알고리듬
	- 충전시, 열화량 정량화
		- Butler-Volmer 식을 통해 열화 속도 계수 (keff) 계산
		- 음극과 전해질 계면의 SEI생성 부반응 도입하여 부반응 전류계산
		-  열화속도 계수가 도출되면 B-V 식을 통해 역으로 열화량 계산 가능
	- 기본 식![[Pasted image 20251212092614.png]]
	- LUT (LookUp Table) 업데이트
		- 충전 전류별 simulation data 생성하여 한계 전압 도출 조건에서 초기 LUT 생성 : 초기 LUT로 부터 충전 효율(열화량 감소/충전시간 증가) 높은 방향으로 최적화
			- figure
				![[Pasted image 20251212092728.png]]
	- ISC detect
		- figure
			![[Pasted image 20251212093554.png]]
			![[Pasted image 20251212093108.png]]
			- ![[Pasted image 20251212093520.png]]
## 상세 모델 식
![[Pasted image 20251212093923.png]]
![[Pasted image 20251212093941.png]]
![[Pasted image 20251212093955.png]]
![[Pasted image 20251212094012.png]]
![[Pasted image 20251212094027.png]]

## 파라미터 자동 추정 적용 알고리듬
- 구조
	![[Pasted image 20251212094116.png]]
- 세부 기술
	 - Diffusivity 특성을 고려한 차원 축소 기술(Anchor Point)
	 - 상위 결과를 이용하여 Boundary를 좁혀 추가로 최적화를 진행하는 Adaptive Boundary 기술
	 - SOC 영역별 오차 민감도를 최대화 하기 위한 Incremental Method
		 ![[Pasted image 20251212094255.png]]
		 ![[Pasted image 20251212094322.png]]
		 ![[Pasted image 20251212094354.png]]
- RSOC 개념도
		- figure
			![[Pasted image 20251212094433.png]]
# 내부단락기준
- 자사
	- 내부 단락 저항을 기준으로 3-level alarm 설정
	- Level 1 (500Ω): 학계/업계 최고 수준의 Soft-short 감지 성능 반영
	- Level 2 (100Ω): 내부 단락으로 인한 누설 전류 급증 수준
	- Level 3 (20Ω): PS 내부 단락 이슈 기반  (SET Log 데이터 기반 산출
- 타사
	※ 참고, 타사 단락 단계에 따른 운영안
	- 0 = 내부 단락 없음 (내부 단락 저항 500Ω 이상), 정상
	- 1 = 내부 단락 1단계 (내부 단락 저항 500Ω~50Ω), 경고
	- 2 = 내부 단락 2단계 (내부 단락 저항 50Ω~25Ω) , 시스템 차단
	- 3 = 내부 단락 3단계 (내부 단락 저항 25Ω 이하)
	- 즉시 충/방전 차단 후 서비스 센터 방문 권고
	![[Pasted image 20251212094802.png]]



# ECT Output
|          |             |         |              |                                                                                              |
| -------- | ----------- | ------- | ------------ | -------------------------------------------------------------------------------------------- |
| Category | Output Data | Format  | Normal Range | Detailed Information                                                                         |
| ECT      | CNT         | integer | 0 ~          | The number of ECT-FG operations performed (ectInit + ectRun)                                 |
| SOC      | ectSOC      | integer | 0 ~ 1000     | ECT Calculated SOC (0 : Fully Discharged / 1000 : Fully Charged)                             |
|          | RSOC        | integer | 0 ~ 1000     | Relative SOC  (0 : Fully Discharged / 1000 : Fully Charged)                                  |
|          | SOC_RE      | integer | 0 ~ 1000     | Reported SOC (0 : Fully Discharged / 1000 : Fully Charged)                                   |
|          | SOC_EDV     | Integer | 5 ~          | End of Dicharge Voltage(EDV) (The remaining SOC amount depending on the EDV value)           |
| SOH      | SOH         | integer | 0 ~ 1000     | Fresh : 1000 (Calculated by SOH_dR,SOH_CA,SOH_X)                                             |
|          | SOH_dR      | integer | 0 ~ 1000     | Increased SEI resistance (Fresh : 0)                                                         |
|          | SOH_CA      | integer | 1000 ~ 0     | Cathode capacity (Fresh : 1000)                                                              |
|          | SOH_X       | integer | 0 ~ -1000    | Balance Shift (Fresh : 0 )                                                                   |
| ISD      | SC_VALUE    | integer | 0 ~          | Short Circuit Detection Value                                                                |
|          | SC_SCORE    | integer | 0 ~ 5        | Short Circuit Detection judgment Value (0,1,2: Not short /  3,4 : short /  5 : Non-judgment) |
|          | SC_V_Acc    | integer | 0 ~          | Short Circuit Detection Accumulation Value                                                   |
|          | SC_V_Avg    | float   | 0 ~          | Short Circuit Detection Average Value                                                        |
| Adaptive | LUT_VOL0    | float   | 3.3 ~ 4.5    | Fast Charge Look Up Table Voltage                                                            |
|          |             |         |              | (Within the battery voltage range)                                                           |
|          |             |         |              | ※ If the charging step does not exist, the value is 0.                                       |
| ECT      | T_move      | float   | ° C          | Moving average temperature                                                                   |

| Output Name     | Node Name           |
|-----------------|---------------------|
| CNT             | ECT_CNT             |
| T_MOVE          | ECT_T_MOVE          |
| ectSOC          | ECT_ASOC            |
| RSOC            | ECT_RSOC            |
| SOC_RE          | ECT_SOC_RE          |
| SOC_EDV         | ECT_SOC_EDV         |
| SOH             | ECT_SOH             |
| SOH_dR          | ECT_SOH_dR          |
| SOH_CA          | ECT_SOH_CA          |
| SOH_X           | ECT_SOH_X           |
| Anode_Potential | ECT_Anode_Potential |
| SC_VALUE        | ECT_ISD_Value       |
| SC_SCORE        | ECT_ISD_Score       |
| SC_V_Acc        | ECT_ISD_Vacc        |
| SC_V_Avg        | ECT_ISD_Vavg        |
| LUT_VOLT0       | ECT_AD_Step0        |
| LUT_VOLT1       | ECT_AD_Step1        |
| LUT_VOLT2       | ECT_AD_Step2        |
| LUT_VOLT3       | ECT_AD_Step3        |

## 관련 문서

- [[Electrochemical parameter]] (Project/Battery_Research)
- [[배터리 QPA(Quality Process Audit)]] (Project/Battery_Research)
- [[코인셀 SOP]] (Project/Battery_Research)
