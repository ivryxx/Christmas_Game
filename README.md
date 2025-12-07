# 🎄 Christmas Mixed-Reality Game 🎄

웹캠 한 대만 있으면 입 모양과 손 제스처로 즐길 수 있는 증강현실 크리스마스 게임입니다. 입을 크게 벌려 선물/사탕/오너먼트들을 먹고, 폭탄은 피하면서 점수를 올리세요. 동시에 손 제스처로 화면 전체 파티클을 제어하며 보너스를 노릴 수 있습니다.

## 📌 개요
- **플랫폼**: Python 3.9+, OpenCV, MediaPipe (Face Mesh + Hands)
- **입력 장치**: 기본 웹캠 1대
- **주요 상호작용**
  1. 입 중앙 좌표와 벌림 비율 → 아이템 충돌 판정
  2. 손 제스처 → 보너스 점수 + 파티클 확장/수축 제어
  3. 키보드/마우스 → 난이도 선택, 일시정지/재시작 등
 
## 🎥 Demo
[▶ Click to watch the demo video] (https://youtu.be/P8N1cDmkpI4)
<img width="600" height="340" alt="스크린샷 2025-12-07 오후 9 44 53" src="https://github.com/user-attachments/assets/d4146f8f-f76c-4035-b64e-50f54ab1eca5" />
<img width="600" height="340" alt="스크린샷 2025-12-07 오후 9 44 11" src= "https://github.com/user-attachments/assets/34e87a07-e64a-4dd7-b598-6c414188ffa2" />

<img width="600" height="340" alt="스크린샷 2025-12-07 오후 9 44 11" src ="https://github.com/user-attachments/assets/8cae568d-d01e-4de7-9708-ca9a484ba6c4"/>

<img width="600" height="340" alt="스크린샷 2025-12-07 오후 9 44 11" src="https://github.com/user-attachments/assets/6f540ed5-1721-4827-b642-81b294f2711c" />

<img width="600" height="340" alt="스크린샷 2025-12-07 오후 9 44 11" src="https://github.com/user-attachments/assets/3e01956a-118b-40cb-8190-1c2945fc8523" />

## 📂 목차
1. [주요 특징](#주요-특징)
2. [설치 방법](#설치-방법)
3. [실행 방법](#실행-방법)
4. [게임 플레이 가이드](#게임-플레이-가이드)
5. [아이템 정보](#아이템-정보)
6. [제스처 시스템](#제스처-시스템)
7. [조작/단축키](#조작단축키)
8. [기술 아키텍처](#기술-아키텍처)
9. [프로젝트 구조](#프로젝트-구조)
10. [커스터마이징 팁](#커스터마이징-팁)
11. [문제 해결 가이드](#문제-해결-가이드)

## 주요 특징
- **난이도 선택 랜딩 페이지**: EASY/NORMAL/HARD 버튼과 숫자 키(1/2/3)로 즉시 선택, 클릭 UI가 파티클 딤과 분리돼 명확하게 눌립니다.
- **입 기반 충돌 시스템**: MediaPipe Face Mesh 468개 랜드마크 중 입 중앙(13,14)을 추적해 정규화된 mouth ratio로 입 벌림 여부를 판정합니다.
- **다채로운 수집 아이템**: Present, Candy Cane, Ginger Cookie, Jingle Bell이 랜덤 속도로 떨어지며 난이도 배수 점수를 제공합니다. Coal은 피해야 하는 hazard입니다.
- **실시간 HUD**: 좌측 상단에 Mouth Ratio와 상태, 우측 상단에 Score/Level/Mode, 좌측 하단에는 수집 현황, 중앙에는 피드백 메시지가 표시됩니다.
- **손 제스처 보너스**: PALM/PEACE/FIST 중 하나를 요청하며, 맞추면 `+40 × 난이도 배수` 점수와 함께 화면 전체 파티클 폭발이 발생합니다. 두 손을 벌리거나 한 손을 핀치하면 파티클 필드가 확장·수축합니다.
- **시각 효과**: 배경 딤, 라이프 배지(하트), 손실 시 화면 플래시, 입수집/미스 피드백, 게임 오버 페이드, 파티클 버스트 등으로 시각적 몰입도를 높였습니다.

## 설치 방법
```bash
git clone <REPO_URL>
cd Christmas_Game
python -m venv .venv
source .venv/bin/activate   # Windows는 .venv\Scripts\activate
pip install -r requirements.txt
```

## 실행 방법
```bash
python src/main.py
```
1. 웹캠 접근 권한을 허용한 뒤 창이 열리면 난이도 버튼을 클릭(또는 `1/2/3` 키)하여 시작합니다.
2. 게임 중 `p`로 일시정지, `r`로 (게임오버 상태에서) 재시작할 수 있습니다.
3. `q`를 누르면 프로그램을 종료합니다.

## 게임 플레이 가이드
- **입 위치 = 플레이어 위치**: 카메라를 정면으로 보고 입 중앙이 화면 가상의 캐릭터 역할을 합니다.
- **입 벌림 임계값**: Mouth Ratio가 0.18을 초과하면 “COLLECTING!” 상태로 바뀌어 아이템을 먹을 수 있습니다. 임계값은 `src/main.py`의 `MOUTH_OPEN_THRESHOLD`에서 조절 가능합니다.
- **라이프 & 점수**: 기본 3~4개의 하트(난이도에 따라 다름)를 갖고 시작하며, 선물을 놓치거나 석탄에 닿으면 감소합니다. 화면 중앙 피드백 텍스트와 테두리 플래시로 즉시 피드백을 제공합니다.
- **레벨 시스템**: 점수가 threshold를 넘으면 레벨이 올라가며 아이템 속도/스폰 간격이 점점 빨라집니다.
- **게임 오버**: 모든 라이프를 잃으면 페이드된 GAME OVER 화면과 아이템별 수집 요약, Replay/Main Menu 버튼이 표시됩니다.

## 아이템 정보
| 아이템 | 타입 | 기본 점수* | 설명 |
| --- | --- | --- | --- |
| Present | Collectible | 10 | 가장 빈번하게 등장하는 기본 선물 |
| Candy Cane | Collectible | 15 | 사탕지팡이, 배수 점수 적용 |
| Ginger Cookie | Collectible | 20 | 드물지만 높은 점수 |
| Jingle Bell | Collectible | 25 | 새로 추가된 방울, 빠르고 작은 크기 |
| Coal | Hazard | - | 닿으면 라이프 감소 및 경고 메시지 |

\* 실제 얻는 점수 = 기본 점수 × 난이도 배수 (Easy 1.0 / Normal 1.15 / Hard 1.35)

## 제스처 시스템
- **요청 카드**: 좌측 상단에 스페이싱을 둔 카드가 표시되어 현재 요구되는 제스처와 문장형 가이드를 제공합니다 (`Open your hand wide!`, `Make a V/peace sign!`, `Hold up a closed fist!`).
- **파티클 제어**:
  - 두 손 인식 → 손목 사이 거리로 확장 정도 계산 (크게 벌릴수록 파티클 확장)
  - 한 손만 인식 → 엄지/검지 간 거리로 수축 정도 계산 (핀치하면 수축)
- **보너스**: 요청된 제스처를 맞추면 2초간 축하 상태가 유지되며 `BONUS +40` 텍스트와 파티클 폭발이 발생한 뒤 새로운 제스처가 랜덤하게 선택됩니다.

## 조작/단축키
- `마우스 클릭`: 메뉴/리플레이 버튼 선택
- `1 / 2 / 3`: 메뉴에서 Easy / Normal / Hard 선택
- `p`: 일시정지 토글
- `r`: 게임오버 상태에서 즉시 재시작
- `q`: 프로그램 종료

## 기술 아키텍처
- **`filter_logic.py`**: MediaPipe Face Mesh & Hands 초기화, 입-눈 거리 계산(`calculate_mouth_dist`), 손 제스처 판별(`detect_hand_gesture`), PnP 기반 Head Pose 유틸
- **`game_logic.py`**: 게임 상태 머신, 난이도 설정, 아이템 스폰/충돌, 레벨/라이프 관리, HUD 및 파티클 렌더링. `ScreenParticleField`로 전체 배경 파티클, `ParticleBurst`로 보너스 폭발을 구현합니다.
- **`main.py`**: 카메라 캡처 루프, 메뉴 UI, 제스처 카드, 손/입 상태와 게임 로직 연결, 키 입력 처리
- **OpenCV**는 프레임 렌더링과 HUD 합성 담당, **MediaPipe**는 랜드마크 추적에 사용됩니다.

## 프로젝트 구조
```
Christmas_Game/
├── assets/
│   ├── bell.png
│   ├── candycane.png
│   ├── coal.png
│   ├── cookie.png
│   └── present.png
├── requirements.txt
└── src/
    ├── filter_logic.py
    ├── game_logic.py
    └── main.py
```

## 커스터마이징 팁
- **임계값 조정**: `MOUTH_OPEN_THRESHOLD`, 제스처 보너스 점수(`GESTURE_BONUS_POINTS`), 아이템 점수/스폰 비중은 코드 상단 상수로 관리됩니다.
- **커스텀 폰트 사용**: OpenCV 기본 `cv2.putText`는 Hershey 폰트만 지원합니다. 임의의 TTF를 쓰고 싶다면 Pillow의 `ImageDraw`/`ImageFont.truetype()`으로 텍스트 이미지를 만든 뒤 NumPy 배열로 변환해 프레임에 합성하거나, `opencv-contrib-python`의 `cv2.freetype.createFreeType2()`를 사용하세요.
- **파티클/색상 테마**: `ScreenParticleField`의 색상과 `GESTURE_COLORS`를 조정하면 제스처별 색 테마를 쉽게 바꿀 수 있습니다.

## 문제 해결 가이드
- **폰트/문자 깨짐**: OpenCV HUD는 ASCII 기반이므로 한글 문구를 넣으면 깨질 수 있습니다. 필요 시 영어 문구 또는 Pillow 기반 커스텀 렌더링을 사용하세요.
- **버튼 클릭 불가**: 메뉴 상태에서도 제스처 오버레이를 0으로 고정했으므로, 그래도 안 된다면 창이 최상단인지 확인하고 한 번 더 메뉴(`Main Menu`)로 돌아가 새로고침하세요.
- **카메라 인식 실패**: 다른 앱이 웹캠을 점유하고 있거나 OS 권한이 막힌 경우입니다. macOS/Windows의 보안 & 개인정보 설정에서 Python에 카메라 사용 권한을 부여하세요.
- **손 제스처 인식 저하**: 충분한 조명과 단색 배경, 손가락이 겹치지 않는 포즈에서 인식률이 올라갑니다. 두 손을 모두 화면에 넣으면 파티클 확장 효과를 바로 확인할 수 있습니다.

행복한 크리스마스 게임 플레이 되세요! 🎁
