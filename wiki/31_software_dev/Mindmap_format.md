---
title: "Mindmap format"
tags:
  - Development
  - 마인드맵
  - Excalidraw
  - 스크립트
type: reference
status: active
related: []
created: 2025-12-15
updated: 2026-03-17
source: "origin/Mindmap format.md"
---

# Mindmap Format Script (Excalidraw)

Excalidraw 마인드맵을 **left-to-right** 형식으로 자동 정렬하는 스크립트.

## 사용법
- **Root node**: 선택한 요소 중 가장 왼쪽 요소가 루트
- **연결**: Arrow로 parent → children 방향 연결 필수
- **정렬 순서**: Arrow 생성 시간 기준 (Y축)
- 순서 변경 시 화살표 삭제 후 재연결

## 설정 옵션 (Excalidraw Plugin Settings 하단)
- `default gap`: 요소 간격 (기본: 10)
- `curve length`: 연결선 곡선 길이 (기본: 40)
- `length between element and line`: 연결선과 요소 간 거리 (기본: 50)

## 주의사항
- Arrow의 startBinding/endBinding이 해제되면 재연결 후 스크립트 재실행 필요
- **group** 요소는 root node로 사용 불가

## 스크립트 코드

```javascript
let settings = ea.getScriptSettings();
//set default values on first run
if (!settings["MindMap Format"]) {
  settings = {
    "MindMap Format": {
      value: "Excalidraw/MindMap Format",
      description:
        "This is prepared for the namespace of MindMap Format and does not need to be modified",
    },
    "default gap": {
      value: 10,
      description: "Interval size of element",
    },
    "curve length": {
      value: 40,
      description: "The length of the curve part in the mind map line",
    },
    "length between element and line": {
      value: 50,
      description:
        "The distance between the tail of the connection and the connecting elements of the mind map",
    },
  };
  ea.setScriptSettings(settings);
}

const sceneElements = ea.getExcalidrawAPI().getSceneElements();

const defaultDotX = Number(settings["curve length"].value);
const defaultLengthWithCenterDot = Number(
  settings["length between element and line"].value
);
const initAdjLength = 4;
const defaultGap = Number(settings["default gap"].value);

const elements = ea.getViewSelectedElements();
generateTree(elements);

ea.copyViewElementsToEAforEditing(elements);
await ea.addElementsToView(false, false);
```
