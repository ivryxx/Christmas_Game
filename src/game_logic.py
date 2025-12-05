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

# 게임 관리 클래스
class ChristmasGame:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.score = 0
        self.objects = []
        self.spawn_timer = 0
        self.base_spawn_rate = 50 # C30: 기본 스폰 속도
        self.spawn_rate = self.base_spawn_rate 
        self.base_speed = 3
        
        # C30: 레벨 관리 변수 추가
        self.level = 1
        self.score_to_next_level = 100 

        # 이미지 로드를 위한 임시 객체 크기 참조
        obj_size = GameObject(0, 0, 0, '').size 
        
        # 이미지 로드 (C29)
        self.present_img = cv2.imread('assets/present.png', cv2.IMREAD_UNCHANGED)
        self.coal_img = cv2.imread('assets/coal.png', cv2.IMREAD_UNCHANGED)
        
        if self.present_img is None or self.coal_img is None:
            print("ERROR: Could not load game asset images (present.png or coal.png). Using placeholders.")
            self.present_img = np.zeros((obj_size, obj_size, 4), dtype=np.uint8)
            self.coal_img = np.zeros((obj_size, obj_size, 4), dtype=np.uint8)

        # 로드된 이미지를 게임 객체 크기에 맞게 미리 리사이즈
        self.present_img = cv2.resize(self.present_img, (obj_size, obj_size))
        self.coal_img = cv2.resize(self.coal_img, (obj_size, obj_size))


    def _check_level_up(self):
        """C30: 현재 점수를 확인하여 레벨을 올리고 난이도를 조절합니다."""
        if self.score >= self.score_to_next_level:
            self.level += 1
            self.score_to_next_level += 100 + (self.level * 50) # 다음 레벨업 목표 점수 증가
            
            # 하강 속도 증가
            self.base_speed += 0.5 
            
            # 스폰 속도 증가 (숫자가 작을수록 빨라짐)
            if self.base_spawn_rate > 15: # 최소 스폰 간격 제한
                self.base_spawn_rate -= 5
            self.spawn_rate = self.base_spawn_rate


    def check_collection(self, is_mouth_open, mouth_x, mouth_y):
        """입 벌림 상태와 입의 위치를 기준으로 객체와의 충돌을 확인하고 점수를 업데이트합니다."""
        if not is_mouth_open:
            return

        for obj in self.objects:
            if obj.type == 'present' and obj.active:
                
                distance_y = abs(mouth_y - obj.y)
                distance_x = abs(mouth_x - obj.x)
                
                # 충돌 조건: 객체 크기 이내로 가까울 때
                if distance_y < obj.size and distance_x < obj.size: 
                    self.score += 10
                    obj.active = False
                    break 

    def update(self):
        """게임 로직 업데이트 (객체 이동, 제거, 레벨 체크)"""
        self._check_level_up() # C30: 레벨업 체크
        
        # 비활성화된 객체 제거
        self.objects = [obj for obj in self.objects if obj.active]
        
        for obj in self.objects:
            obj.move(self.height)
            
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_rate: # C30: 현재 spawn_rate 사용
            self.spawn_object()
            self.spawn_timer = 0
        
        return len(self.objects)

    def spawn_object(self):
        """새로운 선물 또는 장애물을 무작위로 생성합니다."""
        
        x = random.randint(50, self.width - 50)
        y = -50 
        speed = self.base_speed + random.uniform(-0.5, 1.0) # C30: 현재 base_speed 사용
        obj_type = 'present' if random.random() < 0.7 else 'coal'
        
        new_obj = GameObject(x, y, speed, obj_type)
        self.objects.append(new_obj)
        
    def draw(self, frame):
        """모든 게임 객체와 점수를 프레임에 그립니다."""
        for obj in self.objects:
            img = self.present_img if obj.type == 'present' else self.coal_img
            
            x, y = int(obj.x - obj.size / 2), int(obj.y - obj.size / 2)
            w, h = obj.size, obj.size
            
            # ROI 설정 (이미지 경계를 벗어나지 않도록 보호)
            x_end = min(x + w, self.width)
            y_end = min(y + h, self.height)
            
            # 유효한 영역만 처리
            if x >= 0 and y >= 0 and x < self.width and y < self.height:
                roi = frame[y:y_end, x:x_end]
                
                # 이미지 크기가 ROI 크기와 일치하도록 자르기
                img_to_overlay = img[0:y_end-y, 0:x_end-x]
                
                # 4채널 (Alpha) 이미지를 배경에 오버레이
                if img_to_overlay.shape[2] == 4:
                    alpha = img_to_overlay[:, :, 3] / 255.0
                    inv_alpha = 1.0 - alpha

                    # 채널별로 이미지 오버레이 (알파 블렌딩)
                    for c in range(0, 3):
                        roi[:, :, c] = (roi[:, :, c] * inv_alpha) + (img_to_overlay[:, :, c] * alpha)
                else:
                    # 3채널 이미지일 경우 (오류 발생 시 대비)
                    roi[:] = img_to_overlay
            
        # C30: 점수 및 레벨 정보 표시 업데이트
        score_text = f"SCORE: {self.score}"
        level_text = f"LEVEL: {self.level}"
        
        cv2.putText(frame, score_text, (self.width - 150, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, level_text, (self.width - 150, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)