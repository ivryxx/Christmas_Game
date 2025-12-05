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
        self.size = 80 # C35: 크기 증가 반영 (80)
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
        self.base_spawn_rate = 50 
        self.spawn_rate = self.base_spawn_rate 
        self.base_speed = 3
        
        # C30: 레벨 관리 변수
        self.level = 1
        self.score_to_next_level = 100 
        
        # C32: 라이프 및 상태 변수
        self.max_lives = 3
        self.lives = self.max_lives
        self.game_over = False
        self.paused = False # C34

        obj_size = GameObject(0, 0, 0, '').size 
        
        # C29: 이미지 로드
        self.present_img = cv2.imread('assets/present.png', cv2.IMREAD_UNCHANGED)
        self.coal_img = cv2.imread('assets/coal.png', cv2.IMREAD_UNCHANGED)
        
        if self.present_img is None or self.coal_img is None:
            print("ERROR: Could not load game asset images (present.png or coal.png). Using placeholders.")
            self.present_img = np.zeros((obj_size, obj_size, 4), dtype=np.uint8)
            self.coal_img = np.zeros((obj_size, obj_size, 4), dtype=np.uint8)

        self.present_img = cv2.resize(self.present_img, (obj_size, obj_size))
        self.coal_img = cv2.resize(self.coal_img, (obj_size, obj_size))
        
    def reset_game(self):
        """C34: 게임 상태를 초기화하고 재시작합니다."""
        self.score = 0
        self.objects = []
        self.spawn_timer = 0
        self.spawn_rate = self.base_spawn_rate
        self.base_speed = 3
        self.level = 1
        self.score_to_next_level = 100
        self.lives = self.max_lives
        self.game_over = False
        self.paused = False

    def _check_level_up(self):
        """C30: 레벨을 올리고 난이도를 조절합니다."""
        if self.score >= self.score_to_next_level:
            self.level += 1
            self.score_to_next_level += 100 + (self.level * 50)
            self.base_speed += 0.5 
            
            if self.base_spawn_rate > 15: 
                self.base_spawn_rate -= 5
            self.spawn_rate = self.base_spawn_rate


    def check_collection(self, is_mouth_open, mouth_x, mouth_y):
        """C32: 입 벌림 상태와 입의 위치를 기준으로 객체와의 충돌을 확인하고 점수를 업데이트합니다."""
        if self.game_over:
            return

        for obj in self.objects:
            if obj.active:
                
                distance_y = abs(mouth_y - obj.y)
                distance_x = abs(mouth_x - obj.x)
                
                if distance_y < obj.size and distance_x < obj.size: 
                    obj.active = False
                    
                    if obj.type == 'present':
                        if is_mouth_open: # 입 벌려야 수집 성공
                            self.score += 10
                        else: # 놓침
                            self.lives -= 1
                            if self.lives <= 0: self.game_over = True
                                
                    elif obj.type == 'coal': # 석탄 충돌
                        self.lives -= 1
                        if self.lives <= 0: self.game_over = True
                    break 

    def update(self):
        """게임 로직 업데이트 (객체 이동, 제거, 레벨 체크)"""
        if self.game_over or self.paused: # C34: paused 상태일 때 업데이트 중단
            return
            
        self._check_level_up() 
        
        # 객체 이동 및 화면 밖 객체 체크
        for obj in self.objects:
            if obj.move(self.height) and obj.active:
                if obj.type == 'present': # 선물 놓침 처리
                    self.lives -= 1
                    if self.lives <= 0: self.game_over = True
        
        self.objects = [obj for obj in self.objects if obj.active]
        
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
            img = self.present_img if obj.type == 'present' else self.coal_img
            
            x, y = int(obj.x - obj.size / 2), int(obj.y - obj.size / 2)
            w, h = obj.size, obj.size
            
            x_end = min(x + w, self.width)
            y_end = min(y + h, self.height)
            
            if x >= 0 and y >= 0 and x < self.width and y < self.height:
                roi = frame[y:y_end, x:x_end]
                img_to_overlay = img[0:y_end-y, 0:x_end-x]
                
                if img_to_overlay.shape[2] == 4:
                    alpha = img_to_overlay[:, :, 3] / 255.0
                    inv_alpha = 1.0 - alpha

                    for c in range(0, 3):
                        roi[:, :, c] = (roi[:, :, c] * inv_alpha) + (img_to_overlay[:, :, c] * alpha)
                else:
                    roi[:] = img_to_overlay
            
        # C32: 라이프 아이콘/텍스트 그리기
        lives_text = f"LIVES: {self.lives}/{self.max_lives}"
        cv2.putText(frame, lives_text, (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

        # C30: 점수 및 레벨 정보 표시
        score_text = f"SCORE: {self.score}"
        level_text = f"LEVEL: {self.level}"
        
        cv2.putText(frame, score_text, (self.width - 150, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, level_text, (self.width - 150, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        
        # C34: 일시 정지 메시지 출력
        if self.paused and not self.game_over:
            pause_text = "PAUSED (Press P to resume)"
            cv2.putText(frame, pause_text, (self.width // 2 - 200, self.height // 2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
        
        # C32: 게임 오버 화면 출력
        if self.game_over:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, self.height // 2 - 100), (self.width, self.height // 2 + 100), (0, 0, 0), -1)
            alpha = 0.6
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
            
            game_over_text = "GAME OVER"
            final_score_text = f"Final Score: {self.score}"
            restart_text = "Press R to Restart"
            
            cv2.putText(frame, game_over_text, (self.width // 2 - 150, self.height // 2 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
            cv2.putText(frame, final_score_text, (self.width // 2 - 120, self.height // 2 + 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, restart_text, (self.width // 2 - 150, self.height // 2 + 100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2, cv2.LINE_AA)