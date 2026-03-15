---
title: "Altair Conference"
tags: [Work_Log, 컨퍼런스, Altair]
type: reference
status: active
related:
  - "[[업무_정리]]"
created: 2025-12-15
updated: 2026-03-15
source: "origin/Altair Conference.md"
---

금오공대
섬유 및 피그멘테이션 공정 시뮬레이션 연구 결과 발표
• 엑셀 타입 공정 중 섬유 및 피그멘테이션 공정에 대한 시뮬레이션 연구 결과를 발표.
• 연구는 개발 초기 단계로 시뮬레이션 과정에서 발생하는 문제점 해결 중이며, 일부 결과를 제시.
• 접촉 모델로는 DM 분야에서 널리 사용되는 EPA 모델 중 Hertzian 모델과 JKR 모델을 사용함.

다양한 소재 모델링의 어려움과 해결 방안 모색
• 압축 강도가 높은 배터리 소재 모델링에는 소성 변형까지 고려해야 하며, 이는 JPA 모델의 복잡성을 야기한다.
• JPA 모델 사용 시 파라미터 개수가 과다하여 (최대 69개) 모델링에 어려움이 존재, 60억 개에 달하는 파라미터 조정은 불가능에 가깝다.
• 릴리셜 컴프레션 레이션 테스트, 유니셔 테스트, 로테이팅 드럼 테스트 등 다양한 실험을 통해 문제 해결을 위한 노력을 기울였다.

시뮬레이션 결과 분석 및 모델 비교
• 다양한 문제로 인해 파라멜카드 결과는 제시되지 않았다.
• 현재는 아스트로픽 펀딩 모델을 사용 중이며,  보DV 2 모델 결과를 바탕으로 분석 진행.
• 보DV 2 모델의 표면 거칠기 및 파라미터 개수 문제점을 언급하며,  아스트로픽 볼팅 모델로 전환하여 시뮬레이션을 수행했다.

소재 시뮬레이션 결과 분석
• 액티브 머티리얼과 PTF 두 종류 소재를 사용한 시뮬레이션 진행.
• 100마이크로미터 두께, 50마이크로미터 간격, 2mm 길이 조건에서 시뮬레이션 수행.
• PTFA 뭉침 현상 관찰 및 섬유화 과정 확인, 도전제 첨가 시뮬레이션도 진행.

파이버 커넥티비티 시뮬레이션 결과 분석
• 파이버 커넥티비티 구조 형성 여부 확인을 위해 시뮬레이션 진행.
• 5의 길이에 따른 변화 관찰을 위해 1대8에서 3011대64까지 비율 변경.
• 롤링 시 형상은 큰 의미 없으며, 고온 구조 형성 여부와 롤과의 접착력 등을 분석.

시뮬레이션 결과 분석 및 파라미터 연구
• 2.58mm 결과 도출을 위한 시뮬레이션 진행 및 시간적 확인.
• PTFE 관련 파라미터 (두께, 길이, 웨이트 퍼센티지) 변화에 따른 시뮬레이션 수행.
• 시트 측정 결과(커넥티비티, 유니퍼미티, 오리엔테이션) 분석 및 관련 특성 연구.

5 커넥티비티 분석 결과
• 0.6mm 파일 길이와 0.5mm(2%) 데이터를 사용하여 5 커넥티비티를 분석했습니다.
• 유니퍼미티는 0.1mm보다 0.05mm에서 더 향상되었으며, 웨이트는 하이브리드 두께에 따라 차이가 있었습니다.
• 타이거 오리엔테이션은 위쪽에서는 랜덤하지만 아래로 내려갈수록 방향성을 갖게 됩니다. 로딩 전 측정값은 로딩 후보다 오리엔테이션 값이 더 큽니다.

톨체스터 스틸 측정 결과 분석
• 첫 번째와 마지막 입자를 직선으로 연결하여 각도를 측정하였으며, 휘어짐 등은 제외하였다.
• 톨체스터 스틸을 5곳에서 측정, 0.1mm와 0.05mm 파이버에 대한 결과를 도출하였다. 웨이트 1% 변화에 따른 차이는 크지 않았다.
• 현재 결과 해석은 진행되지 않았으며, 0.1mm에서 1% 웨이트 변화 시 더 큰 차이를 보였다.

실험 과정 및 결과 분석
• 7페이지의 오류 수정 및 TTFE의 랜덤성에 대한 논의가 있었다.
• 입자 덩어리 형태의 초기 상태와 계산 시간 문제로 인한 풀어진 상태의 실험 진행을 비교 분석했다.
• 17페이지의 내용은 양쪽 롤의 상이한 회전 속도를 이용한 실험 결과를 다루고 있으며, 활물질과 PTFE를 제외한 시료를 사용했다.

압축 계획 및 입자 거동 분석
• 노멀 포스와 시험 코스의 압축 계획 경향 차이에 대한 고찰이 필요하다.
• 쇼퍼스 적용 시 입자 거동(유동성 포함)에 미치는 영향과 그 정도에 대한 연구가 중요하다.
• 인션 테스트는 분말 유동성을 결정하는 중요한 실험이며, 노멀 퍼스와 시어 퍼스 모두 고려해야 한다.

섬유화 모델링 개선 방안 모색
• 섬유화 정도에 따른 포기장 몰수 차이 해결을 위한 파티클 모델링 계수 값 조정 방안 모색 중
• 현재 사용 중인 EP 모델의 FZ 제로와 F 링 값 결정 방법 개선 필요성 제기
• 반복적인 실험과 데이터 피팅으로 인한 노가다성 문제점 지적 및 최적 실험 방안 제시 어려움 언급

파라미터 최적화 및 파이버 본딩 모델 연구
• 그레이저가 그레이드 투스를 이용한 건식 넌컨시 파티클에 대한 연구에서 부족한 부분들이 존재함.
• 파라미터 맞춤에 AI 활용 방안 고려, 향후 AI 활용 연구 진행 필요성 제시.
• 파이버 본딩 모델을 이용한 스페어 실린더 타입에 대한 테스트 결과, 파라미터 조정 시 효과적임을 확인.

데이터 변화 추이 분석
• 데이터 값이 크게 감소하지는 않았지만, 일정 수준 감소가 있었다.
• 일자리 감소로 인한 데이터 변화가 있었고, 이는 후에 문제점으로 이어질 수 있다.
• 데이터 변화 추이에 대한 발표가 종료되었다.


#Combining Simulation and Machine Learning
• The session focuses on combining simulation and machine learning.
• This combination addresses complex challenges in various fields.
• Seventy percent of invested products utilize this approach, impacting diverse areas like robotics and materials science.

Edith: High-Performance Material Simulation Software
• Edith is a high-performance software utilizing Arctic technology for simulating and analyzing the behavior of complex materials.
• It helps engineers understand material interactions and optimize equipment design through virtual testing.
• The software benefits various industries by providing insights into material processes and behavior.

Accelerated Product Market Entry via Simulation
• Simulation technology expedites product market launch.
• Reduces reliance on physical testing during scale-up studies.
• Serves diverse sectors, including heavy equipment, battery production, and agriculture.

AI Simulation Advancements
• Significant progress in AI simulation capabilities has been achieved.
• The technology now allows exploration of previously impossible tasks.
• Collaborative research efforts with various partners are expanding the scope of AI simulation.

Simulation and AI in Pharmaceutical Production
• Combining simulation and AI is improving international pharmaceutical manufacturing.
• A case study shows how digital twins solved real-world problems for a pharmaceutical company.
• The pharmaceutical industry faces pressure to deliver products faster and maximize production time.

Manufacturing Process Optimization Trial
• A physical trial to boost a manufacturing unit's capacity by 10% failed.
• The trial aimed to increase production from 30% to 40% of the blender's capacity.
• The failed trial was costly, leading to seeking external assistance for optimization.

Improving Mixing Uniformity in Blending
• A study aimed to understand how to improve mixing uniformity in a blender.
• The focus was on adjusting the feel level and RPM of the blender to achieve the desired outcome.
• A physical and digital twin model was used to simulate and optimize the blending process.

AI-Driven Design Space Exploration
• A virtual design of experiments was used to train a predictive model and an AI model.
• The AI model was used to explore the design space, focusing on the final investigation stage.
• Hyperparameter optimization and DOE tools were employed to generate and analyze data, ultimately determining key performance indicators.

Mixing Performance Study Results
• A study found that 55% filler with 11 RPM provided optimal mixing performance.
• Increasing filler to 75% with 4 RPM did not improve blending uniformity.
• Eighteen virtual experiments using AI models identified best and worst mixing scenarios.

Optimizing Blending Capacity for Improved Performance
• A blending uniformity of 0.8 is the target.
• Fifty-five percent capacity offers the best mixing performance, though sixty percent was used.
• Using sixty percent capacity resulted in significant cost savings and revenue increases within two months.

Successful Project: Significant Cost Savings
• A project completed in two months, achieving sixty percent of its goal.
• Data analysis and physical sampling confirmed predictions, leading to success.
• The project resulted in millions of hours saved and showcased applicability across various industries.

Improving Factory Process Efficiency Through Lifter Optimization
• A factory experienced low efficiency due to high energy consumption in its processes.
• The only modifiable aspect was the lifter design, leading to simulations.
• Twelve lifter designs were tested to improve material handling and prevent material retreat.

Material Influence and Light Design
• The text discusses the impact of materials on a design.
• It mentions a 'guide effect' related to the materials.
• A change in light design is also a subject of discussion.

Optimized Design for Improved Throughput
• An iterative design process led to a final optimized design.
• The optimized design improved drying effectiveness by 29% and reduced energy consumption by 22%.
• The original design was compared to the optimized design, showing significant improvements.

Machine Learning Application in Data Optimization
• A project successfully applied machine learning to optimize data processing.
• The project leveraged machine learning to analyze a large dataset (three thousand data points).
• This approach improved upon previous methods that used fewer data points and allowed for complete optimization.

Data Point Revolution in Flight Design
• A significant increase in the number of data points used in flight design, from a previous range of nine to twelve to a much broader, unspecified range.
• Introduction of a new concept called 'articent remission' for process optimization.
• Focus on efficient use of materials, particularly in capacitors, to improve system effectiveness.

Material Science: Particle Mixing in Battery Manufacturing
• Inconsistent mixing is a common issue in battery production, impacting particle and power characteristics.
• Analysis focuses on particle properties like shape, size, and porosity to optimize the manufacturing process.
• The goal is to determine optimal particle size and distribution for improved battery performance.

Material Flow Optimization using Machine Learning
• The text discusses material flow, specifically focusing on the rheology of a paste-like substance.
• Particle size distribution is identified as a key factor influencing the material's flow properties.
• Machine learning was successfully applied to predict and control the desired material viscosity and particle size distribution.

Edith Release and New Calibration Features
• The upcoming Edith release will include new calibration features.
• Several companies, including European firms, will contribute testing and equipment.
• A new method for calculating collision energy using GP will be implemented.

Leadership in Gender Technology
• A presentation concluded with a final slide highlighting leadership in gender technology.
• The presentation emphasized the team's experience and advancement in supporting customers.
• Key points and the team's expertise were underscored as crucial factors.


#전해액
전기차 배터리 시장 현황 및 기술 개발 동향
• 2014년 이후 전기차 시장 성장과 함께 배터리 수요 증가가 예상되며, 2030년까지 5568만 대의 전기차 등록 전망.
• 국내 배터리 3사의 글로벌 시장 점유율은 높으나, 1차 전지 소재 기술은 미흡하며 특히 전해질 분야는 일본 의존도가 높음.
• 배터리 효율 향상을 위한 하이니켈 양극재, 실리콘계 음극재 연구와 함께 원가 절감 및 양극재, 음극재의 단점을 보완하는 전해질 첨가제 소재 개발이 필요함.

전지 첨가제 개발의 미래: AI 기반 가상 소재 설계
• 전지 첨가제는 용매와 염 1000가지 형태로 구성되며, 계면 안정화에 초점을 맞춘 연구가 진행 중이다.
• AI와 빅데이터 기술을 활용한 가상 소재 설계는 후발 투자자에게 경쟁력을 제공하며, 새로운 첨가제 개발에 필수적이다.
• 2035년까지 300만 톤 이상의 전해질 추가 수요가 예상되며,  멀티 스케일 시뮬레이터 개발을 통한 배터리 성능 예측 모델 구축이 중요하다.

AI 기반 가상 소재 설계 기술 연구
• AI 시뮬레이터 개발 연구를 통해 소재 문제 해결에 힘쓰고 있다.
• 인공지능 모델, 리듀스 오더 모델, 병렬 처리를 위한 마이크로서비스 아키텍처 등을 활용한다.
• 현대자동차, 폭스바겐 등에서도 활발히 연구 중인 가상 소재 설계 기술을 연구하고 있으며,  LG 등과 협업하여 MLOC 형태로 피드백을 받으며 개발 중이다.

배터리 소재 개발 시뮬레이션
• 레이턴트 스페이스에서 물질의 시작점과 목표 지점 간 인터폴레이션을 통해 신규 물질을 생성한다.
• 배터리 생산 과정은 믹싱, 코팅, 캘린더링, 변조, 패키징의 5단계로 구성된다.
• 캘린더링 과정에 초점을 맞춰 전해질 분포 및 침습 방향과 배터리 성능 간의 상관관계를 시뮬레이션한다.

마이크로스트럭처 시뮬레이션 연구
• 마이크로스트럭처의 공급률(프로시티)과 불균일률(토피오시티)의 배터리 영향 분석에 대한 연구 진행.
• 파티클 모델링 및 GOM 모델링을 이용한 EDM 시뮬레이션 수행,  각 파티클의 크기 분포 고려.
• 실제 배터리 제작 규격과 동일한 지오메트리 모델링(0.3mm 세로, 1mm 형태)을 통해 현실적인 시뮬레이션 진행.

시뮬레이션 데이터 분석 결과
• 캘린더링 후 시뮬레이션 결과를 분석하기 위해 다양한 파티클 계수 설정 및 시뮬레이션 환경 변화를 통해 데이터를 수집.
• 1차년도 11000개, 2차년도 21000개의 시뮬레이션 데이터 확보 후, 공극률 및 전도도 영향 분석 시뮬레이션 수행.
• EDM 시뮬레이션 결과를 기반으로, Altair의 AcuSolve를 이용한 3차원 공간 내 전류 침투 과정 시뮬레이션 및 모델링 수행 (전체 EDM 시뮬레이션 결과가 아닌, 상반의 4분의 1 지점 기반).

파티클 크기 변화에 따른 시뮬레이션 결과 분석
• 파티클 크기를 세분화하여 전성도와 전담비에 따른 시뮬레이션 결과를 비교 분석했다.
• 전해질 이동 경로 확인을 위한 3개의 프로브를 설정하고, 전해질 분포의 균일성 및 투과율을 분석하는 이미지 데이터를 획득했다.
• 파티클 크기 변화에 따른 전해질 분포의 차이를 시각화하여, 특정 구간에 전해질이 집중되는 현상을 확인했다.

다층 배터리 시뮬레이션 모델 개발 현황
• 마이크로스트럭처를 중심으로 한 다층 배터리 시뮬레이션 모델 개발 중
• 정형/비정형 데이터, 시계열 데이터 활용한 멀티모달 인공지능 모델 개발 및 성능 예측
• 개발된 시뮬레이터는 2차년도 프로토타입 개발 완료, 금년 말 또는 내년 초 최종 개발 예정

AI 기반 배터리 소재 시뮬레이션 연구
• 인공지능 모델들을 구조화하고 하나의 시뮬레이터로 통합하는 연구가 필요하다.
• 각 단계에서 분자 단위 물질의 합성 가능성 및 이론적 타당성 검증 절차를 수행한다.
• 시뮬레이션 결과와 셀 시험 평가를 교차 분석하여 시뮬레이션 결과의 합당성을 검증한다.

첨가제 시뮬레이션 및 전극 시뮬레이션 연동 연구
• 분자 단위 시뮬레이션 결과와 실제 호르몬 값의 유사성을 확인하고 전문가 피드백을 반영하여 연구 진행 중.
• 분자, 마이크로 구조, 세포 단위 영향 검증의 어려움으로 인해 각 모델의 효용성 검토에 집중.
• 3차년도에는 세포 단위 결과 미확보로 소재 영향 평가는 시간이 필요하며, 현재는 모델 효용성 평가 단계임.


# EDM
EDM을 활용한 배터리 셀 제조 공정 시뮬레이션
• EDM 소프트웨어를 이용한 파티클 모델링 방법론과 두 가지 사례(캘린더링, 노칭 공정) 소개
• 배터리 파우더를 이용한 배터리 셀 제조 공정에 EDM이 사용되는 이유는 마이크로 스트럭처 재현 및 배터리 성능 향상과의 직결성 때문
• 특히 캘린더링 공정에서 롤 압착 후 배터리 셀의 마이크로스트럭처 시뮬레이션에 EDM이 활용됨

JDM을 활용한 입자 모델링 과정
• 구조적 변형 및 스트레스 해소와 유동성 확보를 위한 멀티피스 스위스 접근법을 설명.
• 내장된 파우더 데이터베이스를 이용하여 캘리브레이션 과정 없이 실험값을 바로 적용 가능.
• DEM2 기법을 사용하여 입자 간 접촉력 계산 및 탄성, 점탄성, 소성 등 상황에 맞는 물리 모델 선택 가능

입자 거동 모델링 기법 연구
• 입자의 반력 계산을 위한 컨택 모델을 사용하며, 반복적인 과정을 통해 전체 입자 거동을 나타낸다.
• 파우더 입자의 크기가 작아 모델링에 어려움이 있어 메소스코픽 모델링 기법을 활용하여 컴퓨팅 비용을 고려하여 입자 크기를 조정하고 유사한 거동을 보이는 물리 파라미터를 찾는다.
• 특정 공정(예: 캘린더링)에서는 입자 크기 조정이 어려워 실제 크기를 사용하며, 실험 데이터를 통해 상관관계를 분석하여 물성을 찾는다.

배터리 공정 최적화를 위한 시뮬레이션 및 AI 활용
• 캘린더링 공정을 위한 압축 테스트 및 물성 분석을 수행하고, 하이퍼 스터디를 이용한 자동화를 통해 파라미터 세트를 찾는다.
• 획득된 물성 데이터를 이용하여 임펄스/스케일 시뮬레이션을 진행하고, 믹싱 인덱스 및 프로세스 분포 등의 KPI를 분석한다.
• 분석 결과 데이터를 머신러닝 및 딥러닝 기반의 AI 솔루션(롬 AI)을 통해 공정 최적화에 활용한다.

셀 압축 과정 모델링 연구
• 레퍼런스 캐릭터 기반 모델링으로 셀 압축 과정을 시각화하였다.
• 롤 회전과 전극 이동을 고려한 모델링을 통해 해석 비용을 절감하고 유사한 경계 조건을 확보하였다.
• 200mm 길이, 20mm 폭, 350~200 마이크론 두께의 대규모 셀 모델링을 진행하였다.


픽셀 기반 유체 해석 결과 분석
• 픽셀을 이용한 해석에서 한쪽은 텐자이코스를 적용하고 하부는 제트축으로 픽셀 바닥에 고정하는 방식을 사용했다.
• 솔리드 엘리먼트를 사용하여 가장 아래층에 제트축 고정 조건을 적용하였으며, 바운더리 컨디션에 대한 추가 연구가 필요하다.
• 파티클 포지션 압축, 스트레스 분포, 변형 결과 등을 시각적으로 보여주는 결과를 얻었으며, 미세한 변형을 보기 위해 천 배 스케일업하여 롤에 의한 늘어남을 확인했다.

롤 및 코일 공정 분석 결과
• 폭발연의 불균형적인 익스펜션 및 텐자일 방향 알리미 시트 증가 확인.
• 롤 구조 해석, 열 인가, 프로파일 고려, 브리키지 모델 적용 등 심화 분석 예정.
• 노칭 공정에서 포일 리펙트 로드 파손 및 코일 플라스틱 타치트 트레인 가해 현상 관찰, 공정 조건에 따른 전극 밀도 및 강도 영향 분석.

시뮬레이션 기반 포일 커팅 및 변형 예측
• 포일 커팅 시뮬레이션 결과를 통해 데미지 계산 및 형상 예측이 가능함.
• 레퍼런스 자료와의 비교를 통해 시뮬레이션 결과의 유사성 확인 및 예측 정확도 향상.
• 배터리 특화 기능을 갖춘 시뮬레이션 모델을 이용, 포일 변형 및 커팅에 대한 예측 수행 및 향후 전기화학적 해석 탑재 예정.

압축 거동 모델링 및 파라미터
• 입자 압축 시 탄성 거동 모델을 시험.
• 소성 거동의 주요 파라미터는 P6 모델의 핵심.
• 압축 실험을 통한 파라미터 상관관계 분석.


생기연SDI  요소기술개발팀 구조해석
Modeling of calender ingredients

powder data >> rheometer, shear test

contact force >> 탄성 점성 점탄성

overlap > 반력 양과 방향 결정 > bulk model

실제 입자 스케일 업 해석하지만 거동을 유사하게 해석

믹싱, calendaring, >> stress, strain 은 hyperparameter로 물성 피팅

Roll pressing 과 노칭
▪︎ rheology, 갭 롤 스피드 >> porosity tortuosity connectivity
>> Ed

bulk density

press >> Foil deform 해석

해석 20mm * 200mm ** 350um

solid density 스케일 업 >> 관성이 적다는 가장, computing power save

stress , displacement, porosity

dusting burr 형상 구현

Electrochemical 추후 적용

shear modulus
plastic ratio
