import cv2
import filter_logic as fl
import game_logic as gl
import math
import os
import random

# MediaPipe/TensorFlow 로그 레벨 설정 (경고 숨김)
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# C39: 입 벌림 임계값 정의 (정규화된 비율 기준)
MOUTH_OPEN_THRESHOLD = 0.18 # 입 거리가 눈 사이 거리의 18%를 초과할 때 수집
GESTURE_PROMPT_CENTER = (120, 170)
GESTURE_COLORS = {
    'PALM': (0, 220, 200),
    'PEACE': (255, 160, 240),
    'FIST': (255, 180, 120)
}
GESTURE_INSTRUCTIONS = {
    'PALM': 'Open your hand wide!',
    'PEACE': 'Make a V/peace sign!',
    'FIST': 'Hold up a closed fist!'
}

def main():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    window_name = 'Christmas Game Filter'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # MediaPipe Face Mesh 객체 및 유틸리티 초기화
    face_mesh, mp_drawing = fl.initialize_filter_system()
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cv2.resizeWindow(window_name, frame_width, frame_height)
    
    # ChristmasGame 객체 및 MediaPipe Hands 초기화
    game = gl.ChristmasGame(frame_width, frame_height)
    hand_tracker = fl.initialize_hand_tracker()


    gesture_types = ['PALM', 'PEACE', 'FIST']
    GESTURE_INTERVAL_FRAMES = 240
    GESTURE_SUCCESS_FRAMES = 80
    GESTURE_BONUS_POINTS = 40

    gesture_target = None
    gesture_timer = 0
    gesture_ready = False
    gesture_success_timer = 0

    def start_gesture_cycle():
        nonlocal gesture_target, gesture_timer, gesture_ready, gesture_success_timer
        gesture_target = random.choice(gesture_types)
        gesture_timer = 0
        gesture_ready = True
        gesture_success_timer = 0

    def reset_gesture_cycle():
        nonlocal gesture_target, gesture_timer, gesture_ready, gesture_success_timer
        gesture_target = None
        gesture_timer = 0
        gesture_ready = False
        gesture_success_timer = 0

    def mark_gesture_success():
        nonlocal gesture_timer, gesture_ready, gesture_success_timer
        gesture_timer = 0
        gesture_ready = False
        gesture_success_timer = GESTURE_SUCCESS_FRAMES

    def update_gesture_cycle(detected_gesture):
        nonlocal gesture_timer, gesture_success_timer
        if gesture_target is None:
            return
        if gesture_success_timer > 0:
            gesture_success_timer -= 1
            if gesture_success_timer == 0:
                start_gesture_cycle()
            return
        if gesture_ready and detected_gesture == gesture_target:
            gained = game.apply_hand_bonus(
                gesture_target,
                bonus_value=GESTURE_BONUS_POINTS,
                origin=GESTURE_PROMPT_CENTER
            )
            if gained:
                mark_gesture_success()
                return
        gesture_timer += 1
        if gesture_timer >= GESTURE_INTERVAL_FRAMES:
            start_gesture_cycle()

    menu_active = True
    active_buttons = []

    def set_buttons(buttons):
        nonlocal active_buttons
        active_buttons = buttons

    def launch_mode(mode):
        nonlocal menu_active
        game.start_new_run(mode)
        menu_active = False
        start_gesture_cycle()

    def handle_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP:
            for btn in active_buttons:
                x1, y1, x2, y2 = btn['rect']
                if x1 <= x <= x2 and y1 <= y <= y2:
                    callback = btn.get('callback')
                    if callback:
                        callback()

    cv2.setMouseCallback(window_name, handle_mouse)

    def make_start_callback(mode):
        def _start():
            launch_mode(mode)
        return _start

    def replay_current():
        launch_mode(game.current_difficulty)

    def go_to_menu():
        nonlocal menu_active
        menu_active = True
        reset_gesture_cycle()

    def build_difficulty_buttons():
        configs = [
            ('easy', 'EASY', 'Relaxed gift collecting', (80, 180, 100)),
            ('normal', 'NORMAL', 'Balanced challenge', (255, 150, 60)),
            ('hard', 'HARD', 'Blazing-fast presents', (200, 60, 80))
        ]
        button_width = 280
        button_height = 85
        spacing = 28
        vertical_span = button_height * len(configs) + spacing * (len(configs) - 1)
        start_y = (frame_height // 2) - (vertical_span // 2) + 70
        buttons = []
        for idx, (mode, label, subtitle, color) in enumerate(configs):
            x1 = frame_width // 2 - button_width // 2
            y1 = start_y + idx * (button_height + spacing)
            rect = (x1, y1, x1 + button_width, y1 + button_height)
            buttons.append({
                'label': label,
                'subtitle': subtitle,
                'rect': rect,
                'color': color,
                'callback': make_start_callback(mode)
            })
        return buttons

    def build_replay_buttons():
        button_width = 230
        button_height = 70
        y1 = frame_height // 2 + 200
        spacing = 30
        left_rect = (frame_width // 2 - button_width - spacing // 2, y1, frame_width // 2 - spacing // 2, y1 + button_height)
        right_rect = (frame_width // 2 + spacing // 2, y1, frame_width // 2 + button_width + spacing // 2, y1 + button_height)
        return [
            {
                'label': 'REPLAY',
                'subtitle': 'Try again same mode',
                'rect': left_rect,
                'color': (0, 120, 255),
                'callback': replay_current
            },
            {
                'label': 'MAIN MENU',
                'subtitle': 'Choose difficulty',
                'rect': right_rect,
                'color': (120, 50, 180),
                'callback': go_to_menu
            }
        ]

    def draw_buttons(frame, buttons):
        for btn in buttons:
            x1, y1, x2, y2 = btn['rect']
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), btn['color'], -1)
            cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2, cv2.LINE_AA)
            text_y = y1 + (y2 - y1) // 2 + 8
            cv2.putText(frame, btn['label'], (x1 + 25, text_y), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
            subtitle = btn.get('subtitle')
            if subtitle:
                cv2.putText(frame, subtitle, (x1 + 25, y2 - 12), 
                            cv2.FONT_HERSHEY_DUPLEX, 0.58, (255, 255, 255), 1, cv2.LINE_AA)

    def draw_menu_overlay(frame, title, subtitle):
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame_width, frame_height), (30, 0, 70), -1)
        cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)
        cv2.putText(frame, title, (frame_width // 2 - 260, frame_height // 2 - 220), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, subtitle, (frame_width // 2 - 240, frame_height // 2 - 170), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.95, (255, 220, 220), 2, cv2.LINE_AA)

    def draw_hand_icon(frame, origin, gesture, highlighted):
        x, y = origin
        fill = (0, 220, 200) if highlighted else (180, 180, 200)
        outline = (255, 255, 255)
        palm_top = (x + 15, y + 40)
        palm_bottom = (x + 65, y + 98)
        cv2.rectangle(frame, palm_top, palm_bottom, fill, -1)
        cv2.rectangle(frame, palm_top, palm_bottom, outline, 2)

        if gesture == 'PALM':
            for idx in range(4):
                fx = x + 15 + idx * 12
                cv2.rectangle(frame, (fx, y + 5), (fx + 10, y + 45), fill, -1)
                cv2.rectangle(frame, (fx, y + 5), (fx + 10, y + 45), outline, 1)
        elif gesture == 'PEACE':
            for fx in [x + 20, x + 45]:
                cv2.rectangle(frame, (fx, y + 5), (fx + 10, y + 55), fill, -1)
                cv2.rectangle(frame, (fx, y + 5), (fx + 10, y + 55), outline, 1)
            cv2.rectangle(frame, (x + 27, y + 55), (x + 55, y + 70), (140, 140, 160), -1)
            cv2.rectangle(frame, (x + 27, y + 55), (x + 55, y + 70), outline, 1)
        elif gesture == 'FIST':
            cv2.rectangle(frame, (x + 20, y + 15), (x + 60, y + 70), fill, -1)
            cv2.rectangle(frame, (x + 20, y + 15), (x + 60, y + 70), outline, 2)
            cv2.rectangle(frame, (x + 18, y + 65), (x + 62, y + 85), (140, 140, 160), -1)
            cv2.rectangle(frame, (x + 18, y + 65), (x + 62, y + 85), outline, 1)
        elif gesture == 'ROCK':
            for fx in [x + 20, x + 55]:
                cv2.rectangle(frame, (fx, y + 5), (fx + 10, y + 50), fill, -1)
                cv2.rectangle(frame, (fx, y + 5), (fx + 10, y + 50), outline, 1)
            cv2.rectangle(frame, (x + 28, y + 45), (x + 52, y + 70), (140, 140, 160), -1)
            cv2.rectangle(frame, (x + 28, y + 45), (x + 52, y + 70), outline, 1)

    def draw_gesture_prompt(frame, target, detected, ready, success_timer):
        if target is None:
            return
        box_x1, box_y1 = 20, 80
        box_x2, box_y2 = 280, 270
        overlay = frame.copy()
        cv2.rectangle(overlay, (box_x1, box_y1), (box_x2, box_y2), (20, 30, 70), -1)
        cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
        cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (255, 255, 255), 2, cv2.LINE_AA)

        highlight = success_timer > 0 or (ready and detected == target)
        draw_hand_icon(frame, (box_x1 + 12, box_y1 + 20), target, highlight)

        cv2.putText(frame, "BONUS GESTURE", (box_x1 + 110, box_y1 + 45),
                    cv2.FONT_HERSHEY_DUPLEX, 0.62, (255, 210, 180), 1, cv2.LINE_AA)
        instruction = GESTURE_INSTRUCTIONS.get(target, target)
        cv2.putText(frame, target, (box_x1 + 110, box_y1 + 78),
                    cv2.FONT_HERSHEY_DUPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, instruction, (box_x1 + 20, box_y1 + 125),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (210, 220, 255), 1, cv2.LINE_AA)

        status_y = box_y1 + 180
        if success_timer > 0:
            cv2.putText(frame, f"BONUS +{GESTURE_BONUS_POINTS}", (box_x1 + 30, status_y),
                        cv2.FONT_HERSHEY_DUPLEX, 0.78, (255, 120, 220), 2, cv2.LINE_AA)
        elif ready and detected == target:
            cv2.putText(frame, "MATCH! Hold steady", (box_x1 + 20, status_y),
                        cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 220, 180), 2, cv2.LINE_AA)
        elif ready:
            cv2.putText(frame, "Show this hand pose", (box_x1 + 15, status_y),
                        cv2.FONT_HERSHEY_DUPLEX, 0.6, (200, 220, 255), 1, cv2.LINE_AA)
        else:
            cv2.putText(frame, "New pose incoming...", (box_x1 + 12, status_y),
                        cv2.FONT_HERSHEY_DUPLEX, 0.58, (200, 200, 200), 1, cv2.LINE_AA)


    def compute_overlay_intensity(hand_data):
        landmarks = hand_data.get('landmarks') or []
        if len(landmarks) >= 2:
            wrist1_x, wrist1_y, _ = landmarks[0][0]
            wrist2_x, wrist2_y, _ = landmarks[1][0]
            dist = math.sqrt((wrist1_x - wrist2_x) ** 2 + (wrist1_y - wrist2_y) ** 2)
            val = (dist - 0.15) * 2.3
            return max(0.0, min(1.0, val))
        if len(landmarks) == 1:
            lm = landmarks[0]
            thumb_x, thumb_y, _ = lm[4]
            index_x, index_y, _ = lm[8]
            pinch_dist = math.sqrt((thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2)
            val = (pinch_dist - 0.04) * 5.5
            return max(0.0, min(1.0, val))
        return 0.0

    print("Christmas Game Filter started. Click a button to choose difficulty. Press 'q' to exit. Press 'p' to pause during play.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Ignoring empty camera frame.")
            continue
        
        frame = cv2.flip(frame, 1)

        processed_frame, results = fl.process_frame(frame, face_mesh)
        hand_data = fl.detect_hand_gesture(frame, hand_tracker)
        detected_gesture = hand_data.get('gesture')

        mouth_ratio = 0 # 픽셀이 아닌 비율을 사용
        mouth_y = 0
        mouth_x = frame_width / 2
        is_mouth_open = False
        visualized_frame = processed_frame 

        allow_gameplay = results.multi_face_landmarks and not menu_active

        if allow_gameplay:
            landmarks = results.multi_face_landmarks[0]
            
            # C39: 입 벌림 비율 계산 (정규화)
            mouth_ratio = fl.calculate_mouth_dist(landmarks, frame_width, frame_height)
            
            mouth_landmark = landmarks.landmark[fl.MOUTH_UPPER]
            mouth_y = mouth_landmark.y * frame_height
            mouth_x = mouth_landmark.x * frame_width
            
            # C39: 비율 임계값과 비교
            is_mouth_open = mouth_ratio > MOUTH_OPEN_THRESHOLD
            
            # C38: 필터 로직 없이 processed_frame을 시각화 프레임에 할당
            visualized_frame = processed_frame 

            # 충돌 판정 호출
            game.check_collection(is_mouth_open, mouth_x, mouth_y) 
        else:
            visualized_frame = processed_frame 
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                mouth_landmark = landmarks.landmark[fl.MOUTH_UPPER]
                mouth_y = mouth_landmark.y * frame_height
                mouth_x = mouth_landmark.x * frame_width
                mouth_ratio = fl.calculate_mouth_dist(landmarks, frame_width, frame_height)
                is_mouth_open = mouth_ratio > MOUTH_OPEN_THRESHOLD
        
        buttons_for_frame = []
        overlay_intensity = 0.0
        overlay_color = GESTURE_COLORS.get(detected_gesture) or GESTURE_COLORS.get(gesture_target) or (180, 200, 255)
        if not menu_active:
            overlay_intensity = compute_overlay_intensity(hand_data)
        else:
            overlay_color = (160, 160, 200)
            overlay_intensity = 0.0
        game.set_gesture_overlay(overlay_intensity, overlay_color)

        if not menu_active:
            game.update()
            game.draw(visualized_frame)
            if game.game_over:
                buttons_for_frame = build_replay_buttons()
            update_gesture_cycle(detected_gesture)
        else:
            draw_menu_overlay(visualized_frame, "Christmas Catch", "Open wide to grab the gifts!")
            buttons_for_frame = build_difficulty_buttons()

        if buttons_for_frame:
            draw_buttons(visualized_frame, buttons_for_frame)
        set_buttons(buttons_for_frame)
        
        if not menu_active:
            # 입 벌림 상태 시각화
            status_text = "COLLECTING!" if is_mouth_open else "WAITING"
            color = (40, 40, 255) if is_mouth_open else (0, 200, 0)
            cv2.putText(visualized_frame, status_text, (20, 120), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.9, color, 2, cv2.LINE_AA)
            
            dist_text = f"Mouth Ratio: {mouth_ratio:.3f}"
            cv2.putText(visualized_frame, dist_text, (20, 155), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 210, 0), 2, cv2.LINE_AA)

            draw_gesture_prompt(visualized_frame, gesture_target, detected_gesture, gesture_ready, gesture_success_timer)

        # 최종 프레임 표시
        cv2.imshow(window_name, visualized_frame)

        # -----------------
        # 키 입력 처리 (Pause, Restart)
        # -----------------
        key = cv2.waitKey(5) & 0xFF
        
        if key == ord('q'):
            break
        
        # 'p' 키: 일시 정지/재개 토글
        if key == ord('p') and not menu_active and not game.game_over:
            game.paused = not game.paused
        
        # 'r' 키: 게임 오버 상태일 때 재시작
        if key == ord('r') and not menu_active and game.game_over:
            replay_current()

        if menu_active:
            if key == ord('1'):
                launch_mode('easy')
            elif key == ord('2'):
                launch_mode('normal')
            elif key == ord('3'):
                launch_mode('hard')
        # -----------------

    # 자원 해제
    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()
    hand_tracker.close()

if __name__ == "__main__":
    main()
