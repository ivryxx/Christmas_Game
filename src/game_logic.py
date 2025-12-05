import cv2
import random
import numpy as np

# 게임 객체의 기본 속성을 정의하는 클래스
class GameObject:
    def __init__(self, x, y, speed, type):
        self.x = x
        self.y = y
        self.speed = speed
        self.type = type
        self.size = 50
        self.active = True

    def move(self, height):
        """객체를 아래로 이동시키고 화면 밖으로 나가면 비활성화합니다."""
        self.y += self.speed
        if self.y > height + self.size:
            self.active = False
            return True 
        return False

   def draw(self, frame):
        """모든 게임 객체와 점수를 프레임에 그립니다."""
        for obj in self.objects:
            # 📌 C28: 이미지 오버레이 로직 사용
            img = self.present_img if obj.type == 'present' else self.coal_img
            
            x, y, w, h = int(obj.x - obj.size / 2), int(obj.y - obj.size / 2), obj.size, obj.size
            
            # 4채널 (Alpha) 이미지를 배경에 오버레이
            # 1. 원본 이미지의 해당 영역 추출
            roi = frame[y:y+h, x:x+w]
            
            # 2. 알파 채널 추출
            alpha = img[:, :, 3] / 255.0
            inv_alpha = 1.0 - alpha

            # 3. 채널별로 이미지 오버레이 (알파 블렌딩)
            for c in range(0, 3):
                roi[:, :, c] = (roi[:, :, c] * inv_alpha) + (img[:, :, c] * alpha)

# 게임 관리 클래스
class ChristmasGame:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.score = 0
        self.objects = []
        self.spawn_timer = 0
        self.spawn_rate = 50 
        self.base_speed = 3

    def check_collection(self, is_mouth_open, mouth_x, mouth_y):
        """입 벌림 상태와 입의 위치를 기준으로 객체와의 충돌을 확인하고 점수를 업데이트합니다."""
        if not is_mouth_open:
            return

        for obj in self.objects:
            if obj.type == 'present' and obj.active:
                
                # 충돌 판정 (객체 중앙과 플레이어 캐릭터 중앙의 거리)
                distance_y = abs(mouth_y - obj.y)
                distance_x = abs(mouth_x - obj.x)
                
                # 플레이어 캐릭터(main.py의 파란색 사각형)의 Y축 위치를 고려하여 충돌 조건 설정
                # 여기서는 입의 Y 좌표를 사용하여 입으로 '받아먹는' 형태로 충돌을 감지합니다.
                if distance_y < obj.size and distance_x < obj.size: 
                    self.score += 10
                    obj.active = False
                    break 

    def update(self):
        """게임 로직 업데이트 (객체 이동 및 제거)"""
        # 비활성화된 객체 제거
        self.objects = [obj for obj in self.objects if obj.active]
        
        for obj in self.objects:
            obj.move(self.height)
            
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_rate:
            self.spawn_object()
            self.spawn_timer = 0
        
        return len(self.objects)

    def spawn_object(self):
        """새로운 선물 또는 장애물을 무작위로 생성합니다."""
        
        x = random.randint(50, self.width - 50)
        y = -50 
        speed = self.base_speed + random.uniform(-0.5, 1.0)
        obj_type = 'present' if random.random() < 0.7 else 'coal'
        
        new_obj = GameObject(x, y, speed, obj_type)
        self.objects.append(new_obj)
        
    def draw(self, frame):
        """모든 게임 객체와 점수를 프레임에 그립니다."""
        for obj in self.objects:
            obj.draw(frame)

        cv2.putText(frame, f"SCORE: {self.score}", (self.width - 150, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        
        self.present_img = cv2.imread('assets/present.png', cv2.IMREAD_UNCHANGED)
        self.coal_img = cv2.imread('assets/coal.png', cv2.IMREAD_UNCHANGED)
        
        if self.present_img is None or self.coal_img is None:
            print("ERROR: Could not load game asset images (present.png or coal.png).")
            # 이미지가 로드되지 않으면 기본 크기로 빈 이미지 생성 (오류 방지)
            self.present_img = np.zeros((50, 50, 4), dtype=np.uint8)
            self.coal_img = np.zeros((50, 50, 4), dtype=np.uint8)

        # 로드된 이미지를 게임 객체 크기에 맞게 미리 리사이즈
        self.present_img = cv2.resize(self.present_img, (self.objects[0].size, self.objects[0].size)) 
        self.coal_img = cv2.resize(self.coal_img, (self.objects[0].size, self.objects[0].size))