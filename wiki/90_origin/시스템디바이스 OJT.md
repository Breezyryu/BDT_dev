---
title: 시스템디바이스 OJT
category: General
created: 2025-12-15
---

충전은 처음부터 끝까지 같은 전압, 같은 전류로 지속되는 것이 아니라 단계별로 전압, 전류를 바꾸어가며 진행된다.

각 단계를 충전 구간이라 하며 각각 다음과 같다.

### 1.1.1. Pre Charging 구간 (A 구간)

- 배터리 안정성 확보를 위해 일정 전압 이하에서는 많은 전류를 흘릴 수 없다.
- 저전압의 배터리를 충전 전류를 제한해 충전한다.
- 낮은 전류를 흘리며 전압이 일정 수준 올라가면 조금 더 높은 전류를 흘린다. (Trickle Charge)
- 이 구간에서 UI에 표시되는 잔량은 0%.
- 일정 수준의 전압에 도달하면 다음 단계인 CC 구간으로 넘어간다.

### 1.1.2. CC (Constant Current) 구간 (B 구간)

- 충전 전류가 일정하게 유지되며 충전이 진행된다.
- 충전이 진행되며 전압이 지속적으로 오른다.
- 빠른 충전이 가능하며, 초기 충전 효율이 높다.
- 배터리 전압이 일정 수준의 전압, 즉 완충전압(fv: float voltage)에 도달하면 다음 단계인 CV 구간으로 넘어간다.

### 1.1.3. CV (Constant Voltage) 구간 (C 구간)

- 충전 전압이 일정하게 유지되며 전류가 서서히 감소하는 구간.
- 완충 전압이면 완충 상태일텐데 왜 전류를 바로 떨어뜨려 충전을 중단하지 않는가?  
    전류가 서서히 감소하는 이유는 허전압때문으로, 실제로는 만충전압보다 전압이 적으나 만충전압으로 보이는 것.  
    더 충전이 가능하기 때문에 전류가 서서히 감소.
- CV 구간이 끝난 후 UI에 표시되는 잔량은 100%.

### 1.1.4. Back Charging 구간 (C 구간)

- UI 만충 이후 배터리 효율 확보를 위한 추가 충전 구간.
- UI 만충이 실제 배터리 만충을 의미하지 않는다.
- 배터리 UI는 CV 구간에서 이미 100%가 되었기 때문에 사용자는 충전 중인지 알 수 없다.
- 이 구간이 끝난 후 실제 배터리 만충. 
- 이 만충 지점의 전류(EOC, End Of Current)를 사전에 지정해주어야 한다.  
    즉 이 지점의 배터리를 만충인 것으로 정한 것.

### 1.1.5. Recharging 구간 (D 구간)

- 전압이 일정 전압(restart voltage, recharge voltage) 이하로 떨어지면 다시 재충전을 시작.
- 충전기가 연결되어 있어도 충전기가 아닌 배터리에서 방전되는 케이스가 존재할 수 있다.
    - 충전기에서 반응을 못해주는 전류 로드가 생기는 경우
    - 충전기에서 공급해줄 수 있는 최대 전류 이상의 로드가 생기는 경우

## 1.2. Step Charging

실제 Precharge 구간은 순식간에 끝나고, CC와 CV 구간이 전체 충전 시간의 대부분을 차지.

배터리의 충전량은 전류함수의 시간에 대한 적분값과 같으므로 전류가 줄어드는 CV 구간보다는 CC구간이 더 빠르고 많이 충전된다.

그래서 CC구간을 최대한 늘리기 위해, fv를 여러개로 나누고, 각 fv마다 CC 및 CV 구간을 반복하도록 충전하는 방식을 사용.

각 fv에서의 충전을 step이라 하고, 이와 같은 방식을 step charging이라 한다.

# 2. 기본 용어 정의

### 2.1.1. battery cell

배터리의 기본적인 unit. anode, cathode 사이가 전해질(electrolyte)로 차 있고, 중간에 전기적으로 쇼트가 안나도록 seperator 분리막이 있다.

### 2.1.2. battery pack

우리가 실제 사용하는 배터리. 셀을 하나 또는 여러 개 직렬 혹은 병렬로 접합하고 packaging 한 것. protection circuits을 넣기도 한다.

### 2.1.3. C-rate

보통 우리가 배터리 용량을 말할 때, mAh 단위로 말하는데, 이는 만약 4000mAh의 배터리 용량은 4000mA 전류를 1시간 방전시키면 고갈된다는 뜻.

C-rate는 전류의 양을 말하고 싶은데, 디바이스 마다 탑재한 배터리 용량이 다르니, 1000mA 전류는 4000mAh 배터리에겐 큰 전류는 아니지만 1000mAh 배터리에겐 큰 전류일 수 있다.

그래서 배터리 용량에 맞는 상대적인 전류값을 말하기 위해, 1시간 방전시 고갈되는 전류를 1C로 정함. 즉 4000mAh 배터리에서의 1C = 4000mA.

어떤 배터리든 1C로 방전하면 1시간, 0.5C로 방전하면 2시간, 0.1C로 방전하면 10시간을 사용할 수 있다.

### 2.1.4. SOC (state of charge)

최대용량 대비 현재 배터리 용량의 퍼센트 표현. 충전할 때 UI에 표시되는 %값.

일반적으로 쿨롱 카운트를 활용해 전류를 적분연산해서 계산한다.

### 2.1.5. Energy density (Wh/L)

배터리에게는 에너지를 저장할 수 있는 용량도 있고, 배터리가 차지하는 물리적 부피도 있는데,

배터리가 담을 수 있는 에너지를 부피로 나누어 에너지 밀도를 정의. 특정 부피에서 얼마나 많은 에너지를 저장할 수 있는지 척도가 된다.

### 2.1.6. Float Voltage

배터리는 capacitor와 같이 충전하면 전압이 올라간다. 물통에 깔때기를 통해 물을 넣으면 수위가 올라가는 것 같이 전압이 올라가는데, 

어느 정도 차오르면 깔때기 위로 물이 차오른다. 그때는 물을 넣는 양을 줄여 깔때기의 수위를 유지하면서 물통을 채운다.

배터리도 마찬가지로 일정한 전류세기로 충전을 하며 전압이 오르다가 float voltage (만충전압)에 도달하면 전류를 서서히 떨어뜨리며 충전한다.

### 2.1.7. top off

어느 정도 물통이 다 차면 물을 그만 넣어야 한다. 배터리도 만충이 되면 전류 공급을 중단하는데, 이를 top off라 하고, 보통 충전 전류가 0.05C가 되면 top off 한다.

### 2.1.8. maximum charge current

배터리 충전을 빨리하려면 많은 양의 전류로 충전을 하면 되고 좋겠지만 많은 양으로 충전이 가능하면 그만큼 방전도 많은 양의 전류로 하게 된다.  
또 energe density도 1C, 2C, 3C 배터리로 갈 수록 낮아진다. 배터리 전압이 몇일 때 충전 전류를 몇으로 해라 라는 것이 데이터 시트에 있다.

### 2.1.9. secondary battery

재충전 가능. primary는 방전하고 버리는 것.

### 2.1.10. max voltage

물리적 배터리의 최대 전압. 보통 사용할 때는 50mV 정도씩 마진을 두고 사용

### 2.1.11. nominal voltage

정격 전압, 배터리가 출력할 수 있는 평균적인 전압.

### 2.1.12. 용량 단위

용량은 5000mAh 또는 19.30Wh 로 나타낼 수 있다. mAh는 전류x시간이라 에너지를 뜻하진 않는데, 에너지를 표현하기 위해서는 전력에 시간을 곱해야한다.  
그래서 5000mAh에 정격전압 3.86V를 곱하면 19.3Wh가 나온다.

### 2.1.13. PCM

배터리에 연결된 PCB 기반에는 protection circuits이 있는데, 여기에는 극성이 반대인 mosfet을 한 세트로 한 것을 2세트 두고, 세트마다 컨트롤 IC를 두어 배터리를 보호한다.  
충전에 대해서도, 방전에 대해서도 전압, 전류 각각에 대한 보호 기능을 한다.

- Over charger protection (OVP : Over Voltage Protection)
- Charging OCP(Over Current Protection) (COCP)
- Over discharge protection (UVP : Under Voltage Protection)
- Discharging OCP (DOCP)

# 3. 충전의 이해

## 3.1. battery impedence

배터리를 만충시킨 다음에 0.2C로 일정하게 방전을 시켰을 때, 전압이 떨어지는 양상은 다음과 같다.

만충 전압은 4.4V인데, 방전을 시작하자마자 4.3V로 뚝 떨어진다. 그리고 방전이 많이 됐을 때 전압이 급격하게 떨어지는 모습이다.  
이런 특성을 이용해 배터리는 capacitor와 저항이 있는 단순한 모델로 생각할 수 있다.

## 3.2. 배터리 안에 어떤 저항 성분도 없다면,

데이터시트에 있는 일정한 전류 값으로 충전하고 만충전압에 도달하면 충전을 멈추면 된다.

이 일정한 전류값으로 지속적인 충전을 하는 것을 Constant Current 충전, CC 라고 부른다.

## 3.3. 실제 배터리는 저항 성분이 있다.

실제 배터리는 저항 성분(impedence)가 있기 때문에 배터리의 전압이 만충전압에 다다랐을 때 전류를 끊으면

전류를 끊고 방전을 시작하자마자 바로 전압이 뚝 떨어진다. 충전 중에는 capacitor와 저항에 걸린 전압의 합성으로 보이기 때문.

그래서 만충전압 달성과 동시에 전류를 끊으면 70~80% 수준에서 충전이 멈추게 된다.

![](https://confluence-mx.sec.samsung.net/download/attachments/2378774031/image-2025-7-17_13-16-31.png?version=1&modificationDate=1753345132000&api=v2)

충전이 멈췄을 때의 전압(Open Circuit Voltage)도 전압이 떨어지지 않고 만충전압을 유지하게 하려면

이 전압을 유지한 채로 전류를 줄여나가는 과정이 필요한데, 이 과정을 Constant Voltage 충전, CV 라고 한다.

전류를 줄이면서 사전 설정된 top off 상태임을 판단하는 만큼의 전류(0.05C)까지 떨어지면 만충으로 판단하고 충전을 끊는다.

## 3.4. Pack sensing & Cell sensing

### 3.4.1. Pack sensing

![[Pasted image 20251212081637.png]]![[Pasted image 20251212081629.png]]

배터리 팩 단위로 전압을 측정하여 CC - CV를 하면, 실제 Cell은 만충되지 않았는데 CC가 종료되고 CV가 시작되어 Cell의 만충까지 약 130분이 소요되는 것을 확인할 수 있다.

### 3.4.2. Cell sensing

![[Pasted image 20251212081657.png]]![[Pasted image 20251212081702.png]]

반면 배터리 내부 Cell에 따로 Cell sensing line을 두고, Cell 단위로 전압을 측정하여 CC-CV를 하면, 비교적 CC 구간을 더 길게, CV 구간을 더 짧게 하여 top off 까지 약 110분 소요되는 것을 알 수 있다.
그래서 Cell sensing을 활용하면 더 빨리 배터리를 완충 할 수 있다.

# 4. 충전 회로 기초
![[Pasted image 20251212081725.png]]

Linear Charger의 MOSFET은 가변저항의 역할을 하여 서서히 전류나 전압을 바꾸고, Switching Charger의 MOSFET 2개는 스위치의 역할로 Fully Turn-On / Fully Turn-Off 제어.
배터리 쪽 MOSFET의 경우 Qbat 이라고 하는데, 만충 이후 들어오는 전류를 배터리의 충전이 아닌 시스템 전원 공급을 위해 사용하기 위해 배터리가 만충되면 MOSFET을 off하여 배터리로 들어오지 않고 시스템에 전원 공급.
그것만으로는 시스템의 전원 demand를 충족할 수 없는 경우 다시 이 MOSFET이 on되어 전원을 추가 공급.

# 5. Fast Charging

## 5.1. 1세대 AFC

### 5.1.1. 배경
![[Pasted image 20251212081748.png]]

충전을 하면 벽의 콘센트의 AC 110V / 220V의 전원을 충전기에서 DC 5V로 바꾸고 케이블을 통해 전류가 단말로 들어오는데, Fast Charging을 하려고 충전 Watt수를 올리려 하니 대부분의 케이블이 2A 이하 수준의 전류를 지원.
그래서 2A 수준의 전류에 더 많은 전력을 공급하기 위해 전압을 높여 Fast Charging 시작. 삼성의 1세대 Fast Charging - AFC(Adaptive Fast Charging) - 9V/1.65A, 15W

### 5.1.2. 프로토콜
![[Pasted image 20251212081813.png]]

퀄컴의 Fast Charging 규약인 QC 2.0은 걸어주는 Voltage Level의 조합으로 충전 전압을 세팅할 수 있도록 한 반면, 삼성의 AFC는 데이터 통신을 통해 복잡한 패킷을 주고받을 수 있어 더 많은 충전 전압에 더 많은 선택지가 있고, 전류 세기도 또한 선택할 수 있도록 하였다.

![[Pasted image 20251212081829.png]]

처음 단말과 TA가 붙으면 BC 1.2(USB 규약, 단말 입장에서 지금 연결된 것이 [전원공급 + 데이터통신 / only 전원공급] 인지 확인)를 거치고, High Voltage로 충전이 가능한지 확인하는 과정을 거친 후 패킷 데이터 통신을 통해 양방향으로 정보를 주고 받는다.

5V에서 9V(or 12V)로 승압하도록 프로토콜에 맞게 패킷이 전달되었다면 승압 후 Fast Charging 시작

## 5.2. 2세대 Direct Charging

### 5.2.1. 배경

![[Pasted image 20251212081850.png]]

1세대 AFC는 15W까지밖에 지원을 하지 않았다.

그 이유는 switching charger가 90%의 효율로, 15W 충전시 1.5W가 손실되었다.

우리 회사 단말의 경우 1.4W 파워 손실 시 단말 표면의 hotspot 온도가 38도 정도. 우리 회사 표면 온도 규정이 38도.

간당간당하기 때문에 더 높일 수 없었다. 동일한 방식에 40W로 올리면 온도가 60도 넘는다. 

그래서 Switching charger 대신 효율이 좋은 voltage divider를 사용.

대신 이 voltage divider는 전압 수준을 원하는 대로 바꿀 수 없고, 2:1 등 정해진 비율로만 동작한다.

그래서 충전을 TA가 직접 하고, voltage divider는 bypass만 해준다. 그래서 direct charger 라고도 부른다.

  

TA에서 9V/3A가 공급되면 배터리에 전달되는 것은 4.5V/6A가 되어 6A 충전이 가능해지고, 더 빠른 충전이 가능하다.

그래서 일반적인 3A까지 커버 가능한 케이블로도 25W 이상의 Fast Charging이 가능해졌다.

또한 switching charger와 달리 회로상에 inductor가 없고, 파형도 손실이 덜한 파형이 나오는 등 효율이 좋아 96%가 넘는 효율을 보여주고,

40W 충전 시 1.4W 손실되어 당사 표면 온도 규정 최댓값에 도달하는 수준.

### 5.2.2. Direct Charging Methods
![[Pasted image 20251212081912.png]]
2:1만 있는 것은 아니고, 1:1, 2:1, 2:2 등의 direct charging 방식이 있다.

처음 만들어진 direct charger는 정말 들어오는 그대로 배터리에 전달하는 것이었다. (1:1)

그래서 만약 높은 전류의 충전을 하려면 TA와 연결된 케이블도 해당 전류를 전달할 수 있는 것을 사용해야 한다.

2:2 방식은 들어오는 전류를 그대로 들여보내는 대신 배터리를 반으로 나누어 직렬로 연결해 사용하는 방식이다.

ex) 4000mAh의 배터리를 6A로 충전 : 1.5C / 절반으로 나눈 2000mAh의 배터리를 3A로 충전 : 1.5C.

즉, 더 적은 전류로도 C-rate를 유지할 수 있다.

하지만 이 2개의 배터리를 직렬로 연결하면 전압이 2배가 되고, 2배의 전압을 시스템에서 받아들일 수 없기 때문에,

전압을 낮추기 위한 추가적인 회로를 탑재해야 하고, 그 결과 방전시에 거쳐야 하는 추가적인 단계로 인한 효율 저하가 있다.

  

### 5.2.3. 프로토콜

프로토콜의 경우 기존의 방식으로는 감당할 수 없다.

TA가 직접 충전을 컨트롤 해야 하기 때문에 더 섬세하고 더 복잡한 데이터 통신이 필요.

그래서 USB PD(Power Delivery) 통신을 채택. 산업 표준.

USB 3.0에서 지원하는 PPS(Programmable Power Supply) 또한 활용.

단말과 TA사이의 데이터 통신을 통해 TA 출력 전압을 20mV step, 출력 전류를 50mA step으로 세세하게 컨트롤 할 수 있다.




# Graphite anode vs Si anode

anode: 음극재 / Graphite: 흑연 / Si: 실리콘

배터리의 음극재로 어떤 소재를 사용하는 가에 따라 배터리 특성이 크게 달라진다.

|이론 용량|372 mAh/g|3579 mAh/g|
|부피 팽창률|약 10% 미만|약 300% 이상|
|전기 전도도|높음 (금속 수준)|낮음 (반도체 수준)|
|수명 특성|안정적 (수천 사이클)|팽창/수축 반복 → 파손/수명저하|
|가격/가공성|저렴, 성숙한 기술|고가, 가공 어려움|
|리튬 확산 속도|느림|빠름|

  

크기가 큰 배터리를 쓸수록 용량도 늘고 좋지만 제품의 크기를 무한정 키울 수는 없다.

더 적은 크기에 더 많은 용량의 소재인 Si 배터리 쪽으로 발전해가야 한다.

하지만 Swelling 등의 위험이 기존 대비 커지기 때문에,

Graphite와 Silicon을 섞어 사용, 또는  
Si-C Composite 등의 합성 음극을 사용하는 등 용량을 적게 늘리고, 위험성도 적게 늘리는 방향으로의 연구

팽창할 공간을 미리 비워 놓는다던가,  
코팅 기술을 발전시키는 등 Swelling을 방지하는 새로운 방법들을 도입

위 같은 노력이 진행중이다.

  

Swelling 위험이 높아진다는 것은 바뀔 수 없는 사실이기 때문에,

이 Swelling을 미리 감지할 수 있다면 좋을 것이다.

하지만 현재 이런 솔루션은 우리 제품에 없다!

이런 걸 할 수 있는 구조가 SBP이다.

  

# SBP (Smart Battery Pack)

충전 제어 기능과 보호 기능이 있는 칩이 탑재돼 있으며 정확한 잔량을 체크할 수 있는 배터리

→ 간단히, Fuel Gauge가 내장된 Battery Pack
![[Pasted image 20251212082548.png]]
## Smart Battery vs Dumb Battery

기존 배터리

- 2개의 PCM (Protecting Circuit Module)
- 실제 배터리 셀
- 단말 IFPMIC 속 FG와 연결할 외부 단자 필요

스마트 배터리

- 배터리 팩 내부의 FG가 1st PCM 역할 + 2nd PCM
- 실제 배터리 셀
- FG가 배터리 내부에 있으므로 배터리팩 이원화 용이 (chemistry 내장), 외부 단자 X, i2c로 통신
- System side에서 배터리 파라미터 관리 불필요
    
- 내부 IC가 있으므로 S/W 적 Protection 가능
- 내부 FG는 배터리 전원을 공급 받을 수 있기에 AP가 꺼져 있어도 동작 가능 (추정)
    - Always “in-sync” with the battery (no initial SOC error)
        
        Constant and precise SOC and SOH monitor
- Host side에서의 개발/검증 비용 및 burden 감소 → pack maker에서 관리
    - Cell characterization / SOC tuning / Failure analysis

  

## Smart Battery System

![[Pasted image 20251212082603.png]]
- Smart Battery
    - Host에 gauging 정보 제공
    - Critical events 검출 시 Smart Charger, Host에 Broadcast
        - over current, over voltage, over temperature, ... 
        - Terminate Charge Alarm (TCA), Terminate Discharge Alarm (TDA), Remaining Capacity Alarm (RCA),   
            Fully Charged (FC), Fully Discharged(FD)
- Smart Charger
    - 주기적으로 Smart Battery를 polling 하여 battery charging 특성에 맞게 출력 조절
    - sec_battery.c 같은 역할
- Host
    - Smart Battery 정보를 User에게 제공
    - Smart Battery 정보를 power management에 활용

  

  

※ IFPMIC + Smart Battery면 FG가 중복 탑재?

→ 어쩔 수 없다! 그만큼 Smart Battery 쓰는 이점이 크다.