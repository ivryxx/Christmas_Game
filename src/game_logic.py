import cv2
import math
import os
import random
import numpy as np


class ParticleBurst:
    def __init__(self, center_x, center_y, color, count=70):
        self.particles = []
        self.center_x = center_x
        self.center_y = center_y
        for _ in range(count):
            velocity = (
                random.uniform(-3.5, 3.5),
                random.uniform(-4.5, -1.5)
            )
            life = random.randint(18, 35)
            size = random.randint(3, 6)
            self.particles.append({
                'x': center_x + random.uniform(-10, 10),
                'y': center_y + random.uniform(-10, 10),
                'vx': velocity[0],
                'vy': velocity[1],
                'life': life,
                'max_life': life,
                'size': size,
                'color': color
            })

    def update(self):
        active = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.25 # gravity
            p['life'] -= 1
            if p['life'] > 0:
                active.append(p)
        self.particles = active

    def draw(self, frame):
        for p in self.particles:
            alpha = max(0.1, p['life'] / p['max_life'])
            color = tuple(min(255, int(c * (0.6 + 0.4 * alpha))) for c in p['color'])
            cv2.circle(frame, (int(p['x']), int(p['y'])), p['size'], color, -1, cv2.LINE_AA)

    def is_finished(self):
        return len(self.particles) == 0


class ScreenParticleField:
    def __init__(self, width, height, count=520):
        self.width = width
        self.height = height
        self.center_x = width / 2
        self.center_y = height / 2
        self.particles = []
        self.intensity = 0.0
        self.color = (200, 200, 255)

        radius_limit = min(width, height) * 0.75
        for _ in range(count):
            radius = random.uniform(40, radius_limit)
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.003, 0.012)
            size = random.uniform(2.0, 4.5)
            x = self.center_x + math.cos(angle) * radius
            y = self.center_y + math.sin(angle) * radius * 0.45
            self.particles.append({
                'radius': radius,
                'angle': angle,
                'speed': speed,
                'size': size,
                'x': x,
                'y': y,
                'phase': random.uniform(0, math.pi * 2),
                'alpha': 0.3
            })

    def update(self, factor, color):
        self.intensity = factor
        if color is not None:
            self.color = color

        swirl = 0.7 + factor * 1.6
        for p in self.particles:
            p['angle'] += p['speed'] * swirl
            wave = math.sin(p['phase'] + p['angle'] * 1.5)
            radius = p['radius'] * (0.7 + factor * 1.3)
            target_x = self.center_x + math.cos(p['angle']) * radius + wave * 30 * factor
            target_y = self.center_y + math.sin(p['angle']) * radius * 0.55 + math.cos(p['angle'] * 2) * 35 * factor
            p['x'] += (target_x - p['x']) * 0.1
            p['y'] += (target_y - p['y']) * 0.1
            p['alpha'] = 0.2 + 0.7 * factor + 0.1 * math.sin(p['angle'] + p['phase'])

    def draw(self, frame):
        overlay = np.zeros_like(frame)
        base_color = np.array(self.color, dtype=np.float32)
        for p in self.particles:
            size = max(1, int(p['size'] * (1 + self.intensity * 1.9)))
            color_shift = 35 * math.sin(p['angle'] + p['phase'])
            color = tuple(int(np.clip(c + color_shift, 0, 255)) for c in base_color)
            cv2.circle(overlay, (int(p['x']), int(p['y'])), size, color, -1, cv2.LINE_AA)

        alpha = min(0.65, 0.25 + self.intensity * 0.5)
        cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)

# 게임 객체의 기본 속성을 정의하는 클래스
class GameObject:
    def __init__(self, x, y, speed, type):
        self.x = x
        self.y = y
        self.speed = speed
        self.type = type
        self.size = 120 # C35: 크기 증가 반영 (80)
        self.active = True

    def move(self, height):
        """객체를 아래로 이동시키고 화면 밖으로 나가면 비활성화합니다."""
        self.y += self.speed
        if self.y > height + self.size:
            # 객체가 화면 밖으로 나갔으나, 아직 수집되지 않은 경우
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
        self.paused = False 

        # 📌 C40: 피드백 메시지 변수 추가
        self.feedback_text = ""
        self.feedback_color = (0, 0, 0) # BGR
        self.max_feedback_time = 30 # 30프레임 (약 0.5초) 동안 표시
        self.feedback_timer = 0

        # 라이프 감소 시 화면 플래시 관련 변수
        self.damage_flash_duration = 12
        self.damage_flash_timer = 0
        self.damage_flash_color = (0, 0, 255)

        obj_size = GameObject(0, 0, 0, '').size 

        # 아이템 정의 및 이미지 로드 설정
        self.asset_dir = os.path.join(os.path.dirname(__file__), 'assets')
        self.item_properties = {
            'present': {
                'category': 'collectible',
                'score': 10,
                'display_name': 'Present',
                'asset': 'present.png',
                'fallback_color': (0, 200, 0),
                'spawn_weight': 0.35
            },
            'candycane': {
                'category': 'collectible',
                'score': 15,
                'display_name': 'Candy Cane',
                'asset': 'candycane.png',
                'fallback_color': (0, 105, 255),
                'spawn_weight': 0.2
            },
            'cookie': {
                'category': 'collectible',
                'score': 20,
                'display_name': 'Ginger Cookie',
                'asset': 'cookie.png',
                'fallback_color': (60, 180, 255),
                'spawn_weight': 0.15
            },
            'bell': {
                'category': 'collectible',
                'score': 25,
                'display_name': 'Jingle Bell',
                'asset': 'bell.png',
                'fallback_color': (60, 255, 255),
                'spawn_weight': 0.1
            },
            'coal': {
                'category': 'hazard',
                'penalty': 1,
                'display_name': 'Coal',
                'asset': 'coal.png',
                'fallback_color': (40, 40, 40),
                'spawn_weight': 0.2
            }
        }

        self.item_images = {}
        for item_type, props in self.item_properties.items():
            asset_path = os.path.join(self.asset_dir, props['asset']) if props.get('asset') else None
            self.item_images[item_type] = self._load_item_image(asset_path, obj_size, props.get('fallback_color', (255, 255, 255)))

        self.collectible_types = [key for key, props in self.item_properties.items() if props.get('category') == 'collectible']
        self.collection_counts = {item_type: 0 for item_type in self.collectible_types}

        self.particle_effects = []
        self.sky_particles = ScreenParticleField(width, height)
        self.gesture_overlay_target = 0.0
        self.gesture_overlay_factor = 0.0
        self.gesture_overlay_color = (200, 200, 255)

        self.difficulty_settings = {
            'easy': {
                'base_speed': 2.8,
                'speed_variance': (0.3, 1.2),
                'spawn_rate': 70,
                'max_lives': 4,
                'score_multiplier': 1.0
            },
            'normal': {
                'base_speed': 3.6,
                'speed_variance': (0.4, 1.8),
                'spawn_rate': 55,
                'max_lives': 3,
                'score_multiplier': 1.15
            },
            'hard': {
                'base_speed': 4.5,
                'speed_variance': (0.6, 2.4),
                'spawn_rate': 42,
                'max_lives': 3,
                'score_multiplier': 1.35
            }
        }
        self.current_difficulty = 'normal'
        self.speed_variance = (0.4, 1.8)
        self.score_multiplier = 1.0
        self.start_new_run(self.current_difficulty)
        
    def reset_game(self):
        """C34: 게임 상태를 초기화하고 재시작합니다."""
        self.score = 0
        self.objects = []
        self.spawn_timer = 0
        self.spawn_rate = self.base_spawn_rate
        self.level = 1
        self.score_to_next_level = 100
        settings = self.difficulty_settings.get(self.current_difficulty, self.difficulty_settings['normal'])
        self.max_lives = settings['max_lives']
        self.lives = self.max_lives
        self.game_over = False
        self.paused = False
        self.feedback_timer = 0 # C40
        self.damage_flash_timer = 0
        self.particle_effects = []
        self.gesture_overlay_target = 0.0
        self.gesture_overlay_factor = 0.0
        for item in self.collectible_types:
            self.collection_counts[item] = 0

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
        """C32, C40: 입 벌림 상태와 입의 위치를 기준으로 객체와의 충돌을 확인하고 점수를 업데이트합니다."""
        if self.game_over:
            return

        for obj in self.objects:
            if not obj.active:
                continue

            distance_y = abs(mouth_y - obj.y)
            distance_x = abs(mouth_x - obj.x)

            if distance_y < obj.size and distance_x < obj.size:
                obj.active = False
                props = self.item_properties.get(obj.type, {})
                category = props.get('category', 'collectible')
                display_name = props.get('display_name', obj.type.title())

                if category == 'collectible':
                    if is_mouth_open:
                        score_gain = int(props.get('score', 10) * self.score_multiplier)
                        self.score += score_gain
                        self._apply_feedback(f"{display_name}! (+{score_gain})", (0, 255, 0))
                        if obj.type in self.collection_counts:
                            self.collection_counts[obj.type] += 1
                    else:
                        self._apply_feedback(f"MOUTH CLOSED! Missed {display_name}", (0, 165, 255))
                        self._lose_life(flash_color=(0, 165, 255))
                else:
                    penalty = props.get('penalty', 1)
                    self._apply_feedback(f"{display_name}! (-{penalty} Life)", (0, 0, 255))
                    self._lose_life(penalty, flash_color=(0, 0, 255))
                break 

    def update(self):
        """게임 로직 업데이트 (객체 이동, 제거, 레벨 체크)"""
        self.gesture_overlay_factor += (self.gesture_overlay_target - self.gesture_overlay_factor) * 0.08
        self.sky_particles.update(self.gesture_overlay_factor, self.gesture_overlay_color)

        if self.feedback_timer > 0:
            self.feedback_timer -= 1

        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1

        self._update_particle_effects()

        if self.game_over or self.paused: 
            return
            
        self._check_level_up() 
        
        # 객체 이동 및 화면 밖 객체 체크
        objects_to_keep = []
        for obj in self.objects:
            is_off_screen = obj.move(self.height)
            
            if is_off_screen and obj.active:
                props = self.item_properties.get(obj.type, {})
                if props.get('category') == 'collectible':
                    display_name = props.get('display_name', obj.type.title())
                    self._apply_feedback(f"Missed {display_name}!", (0, 165, 255))
                    self._lose_life(flash_color=(0, 165, 255))

                obj.active = False
            
            if obj.active:
                objects_to_keep.append(obj)
                
        self.objects = objects_to_keep
        
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_rate: 
            self.spawn_object()
            self.spawn_timer = 0
        
        return len(self.objects)

    def spawn_object(self):
        """새로운 선물 또는 장애물을 무작위로 생성합니다."""
        
        x = random.randint(50, self.width - 50)
        y = -50 
        variance_min, variance_max = self.speed_variance
        level_bonus = min(self.level * 0.15, 2.5)
        speed = self.base_speed + random.uniform(variance_min, variance_max) + random.uniform(0, level_bonus)
        obj_type = self._choose_spawn_type()
        
        new_obj = GameObject(x, y, speed, obj_type)
        self.objects.append(new_obj)
        
    def draw(self, frame):
        """모든 게임 객체와 점수, 피드백을 프레임에 그립니다."""
        # 배경 딤 및 파티클 필드 오버레이를 먼저 적용해 아이템이 위에 놓이도록 함
        background_overlay = np.zeros_like(frame)
        background_overlay[:] = (30, 10, 40)
        dim_alpha = min(0.6, 0.2 + self.gesture_overlay_factor * 0.35)
        cv2.addWeighted(background_overlay, dim_alpha, frame, 1 - dim_alpha, 0, dst=frame)
        self.sky_particles.draw(frame)

        for obj in self.objects:
            img = self.item_images.get(obj.type, self.item_images.get('present'))
            
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

        self._draw_particle_effects(frame)

        if self.damage_flash_timer > 0:
            intensity = self.damage_flash_timer / self.damage_flash_duration
            alpha = min(0.6, 0.6 * intensity)
            overlay = np.full_like(frame, self.damage_flash_color)
            frame[:] = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        self._draw_hearts(frame)

        # C30: 점수, 레벨, 난이도 정보 표시
        score_text = f"SCORE: {self.score}"
        level_text = f"LEVEL: {self.level}"
        diff_text = f"MODE: {self.current_difficulty.upper()}"
        
        cv2.putText(frame, score_text, (self.width - 240, 70), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.0, (40, 220, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, level_text, (self.width - 240, 110), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, diff_text, (self.width - 240, 150), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (180, 200, 255), 2, cv2.LINE_AA)

        self._draw_collected_summary(frame)
        
        # C34: 일시 정지 메시지 출력
        if self.paused and not self.game_over:
            pause_text = "PAUSED (Press P to resume)"
            cv2.putText(frame, pause_text, (self.width // 2 - 200, self.height // 2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)

        # 📌 C40: 실시간 피드백 메시지 출력
        if self.feedback_timer > 0:
            center_x = self.width // 2
            center_y = self.height // 2 - 150 
            
            scale = 1.5
            thickness = 3
            
            # 텍스트의 중심을 맞추기 위해 텍스트 크기 계산
            (text_w, text_h), baseline = cv2.getTextSize(self.feedback_text, cv2.FONT_HERSHEY_DUPLEX, scale, thickness)
            
            cv2.putText(frame, self.feedback_text, (center_x - text_w // 2, center_y), 
                        cv2.FONT_HERSHEY_DUPLEX, scale, self.feedback_color, thickness, cv2.LINE_AA)

        # C32: 게임 오버 화면 출력
        if self.game_over:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, self.height // 2 - 100), (self.width, self.height // 2 + 100), (0, 0, 0), -1)
            alpha = 0.6
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
            
            game_over_text = "GAME OVER"
            final_score_text = f"Final Score: {self.score}"
            restart_text = "Press R to Restart"
            
            cv2.putText(frame, game_over_text, (self.width // 2 - 210, self.height // 2 - 30), 
                        cv2.FONT_HERSHEY_DUPLEX, 1.8, (20, 0, 255), 4, cv2.LINE_AA)
            cv2.putText(frame, final_score_text, (self.width // 2 - 200, self.height // 2 + 30), 
                        cv2.FONT_HERSHEY_DUPLEX, 1.1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, restart_text, (self.width // 2 - 200, self.height // 2 + 80), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 220, 0), 2, cv2.LINE_AA)

            summary_lines = self._get_collected_summary_lines()
            summary_start_y = self.height // 2 + 130
            for idx, line in enumerate(summary_lines):
                cv2.putText(frame, line, (self.width // 2 - 200, summary_start_y + idx * 35), 
                            cv2.FONT_HERSHEY_DUPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)

    def _choose_spawn_type(self):
        total_weight = sum(props.get('spawn_weight', 1) for props in self.item_properties.values())
        pick = random.uniform(0, total_weight)
        cumulative = 0
        for item_type, props in self.item_properties.items():
            cumulative += props.get('spawn_weight', 1)
            if pick <= cumulative:
                return item_type
        return 'present'

    def start_new_run(self, difficulty=None):
        if difficulty:
            normalized = difficulty.lower()
            if normalized in self.difficulty_settings:
                self.current_difficulty = normalized
        self._apply_difficulty(self.current_difficulty)
        self.reset_game()

    def _apply_difficulty(self, difficulty):
        settings = self.difficulty_settings.get(difficulty, self.difficulty_settings['normal'])
        self.base_speed = settings['base_speed']
        self.speed_variance = settings['speed_variance']
        self.base_spawn_rate = settings['spawn_rate']
        self.spawn_rate = self.base_spawn_rate
        self.score_multiplier = settings['score_multiplier']

    def _draw_hearts(self, frame):
        start_x = 30
        heart_spacing = 45
        for idx in range(self.max_lives):
            filled = idx < self.lives
            x = start_x + idx * heart_spacing
            self._draw_heart_shape(frame, (x, 50), 26, filled)

    def _draw_heart_shape(self, frame, center, size, filled):
        x, y = center
        radius = size // 2
        offset = radius // 2
        color = (0, 0, 230) if filled else (70, 70, 90)
        outline_color = (255, 255, 255) if filled else (120, 120, 120)

        cv2.circle(frame, (x - offset, y), radius, color, -1)
        cv2.circle(frame, (x + offset, y), radius, color, -1)
        triangle = np.array([
            [x - radius - offset, y],
            [x + radius + offset, y],
            [x, y + size]
        ], np.int32)
        cv2.fillConvexPoly(frame, triangle, color)

        cv2.circle(frame, (x - offset, y), radius, outline_color, 2)
        cv2.circle(frame, (x + offset, y), radius, outline_color, 2)
        cv2.polylines(frame, [triangle], True, outline_color, 2, cv2.LINE_AA)

    def _draw_collected_summary(self, frame):
        start_x = 20
        start_y = self.height - 140
        cv2.putText(frame, "COLLECTED", (start_x, start_y), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 200, 150), 2, cv2.LINE_AA)
        for idx, item in enumerate(self.collectible_types):
            display_name = self.item_properties[item]['display_name']
            count = self.collection_counts.get(item, 0)
            text = f"{display_name}: {count}"
            cv2.putText(frame, text, (start_x, start_y + 30 + idx * 28), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.7, (200, 255, 200), 1, cv2.LINE_AA)

    def _get_collected_summary_lines(self):
        lines = []
        total = sum(self.collection_counts.values())
        lines.append(f"Total Collected: {total}")
        for item in self.collectible_types:
            display_name = self.item_properties[item]['display_name']
            count = self.collection_counts.get(item, 0)
            lines.append(f"{display_name}: {count}")
        return lines

    def set_gesture_overlay(self, intensity, color=None):
        self.gesture_overlay_target = max(0.0, min(1.0, intensity))
        if color is not None:
            self.gesture_overlay_color = color

    def apply_hand_bonus(self, gesture_name, bonus_value=30, origin=None):
        if self.game_over:
            return 0
        score_gain = int(bonus_value * self.score_multiplier)
        self.score += score_gain
        self._apply_feedback(f"{gesture_name} BONUS! (+{score_gain})", (255, 120, 220))
        if origin is None:
            origin = (self.width // 2, self.height // 2)
        self.trigger_particle_effect(origin, (255, 120, 220))
        return score_gain

    def trigger_particle_effect(self, origin, color):
        x, y = origin
        burst = ParticleBurst(x, y, color)
        self.particle_effects.append(burst)

    def _update_particle_effects(self):
        active_effects = []
        for effect in self.particle_effects:
            effect.update()
            if not effect.is_finished():
                active_effects.append(effect)
        self.particle_effects = active_effects

    def _draw_particle_effects(self, frame):
        for effect in self.particle_effects:
            effect.draw(frame)

    def _apply_feedback(self, text, color):
        self.feedback_text = text
        self.feedback_color = color
        self.feedback_timer = self.max_feedback_time

    def _lose_life(self, amount=1, flash_color=(0, 0, 255)):
        self.lives -= amount
        self.damage_flash_color = flash_color
        self.damage_flash_timer = self.damage_flash_duration
        if self.lives <= 0:
            self.game_over = True

    def _load_item_image(self, path, size, fallback_color):
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED) if path else None
        if path and img is None:
            print(f"WARNING: Could not load asset '{path}'. Using fallback graphic.")
        if img is None:
            img = np.zeros((size, size, 4), dtype=np.uint8)
            img[:, :, :3] = fallback_color
            img[:, :, 3] = 255
        else:
            img = cv2.resize(img, (size, size))

        return img
