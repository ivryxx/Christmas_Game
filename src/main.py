import cv2
import filter_logic as fl
import game_logic as gl
import numpy as np
import os

# MediaPipe/TensorFlow 로그 레벨 설정 (경고 숨김)
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# C39: 입 벌림 임계값 정의 (정규화된 비율 기준)
MOUTH_OPEN_THRESHOLD = 0.18 # 입 거리가 눈 사이 거리의 18%를 초과할 때 수집

def main():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # MediaPipe Face Mesh 객체 및 유틸리티 초기화
    face_mesh, mp_drawing = fl.initialize_filter_system()
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # ChristmasGame 객체 초기화
    game = gl.ChristmasGame(frame_width, frame_height)
    
    player_x = frame_width / 2

    print("Christmas Game Filter started. Press 'q' to exit. Press 'p' to pause. Press 'r' to restart.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Ignoring empty camera frame.")
            continue
        
        frame = cv2.flip(frame, 1)

        processed_frame, results = fl.process_frame(frame, face_mesh)
        
        mouth_ratio = 0 # 픽셀이 아닌 비율을 사용
        mouth_y = 0
        is_mouth_open = False
        visualized_frame = processed_frame 
        rvec = None 

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            
            # C39: 입 벌림 비율 계산 (정규화)
            mouth_ratio = fl.calculate_mouth_dist(landmarks, frame_width, frame_height)
            
            # fl.MOUTH_UPPER 상수 참조 (Y 좌표는 여전히 픽셀 기반)
            mouth_y = landmarks.landmark[fl.MOUTH_UPPER].y * frame_height
            
            # C39: 비율 임계값과 비교
            is_mouth_open = mouth_ratio > MOUTH_OPEN_THRESHOLD
            
            # Head Pose 추정
            rvec, image_points, camera_matrix, dist_coeffs = fl.get_head_pose(landmarks, frame_width, frame_height)
            
            if rvec is not None:
                # Yaw 기반 player_x 계산
                yaw_factor = rvec[1][0]
                max_movement = frame_width * 0.4 
                movement = np.clip(yaw_factor * 200, -max_movement, max_movement)
                player_x = (frame_width / 2) + movement 
                
                # Head Pose 축 시각화 (현재 주석 처리되어 숨겨짐)
                # visualized_frame = fl.draw_head_pose_axis(visualized_frame, rvec, image_points, camera_matrix, dist_coeffs)

            # C38: 필터 로직 없이 processed_frame을 시각화 프레임에 할당
            visualized_frame = processed_frame 

            # 충돌 판정 호출
            game.check_collection(is_mouth_open, player_x, mouth_y) 

        else:
            # 얼굴이 감지되지 않을 때
            visualized_frame = processed_frame 
            
        # -----------------
        # 게임 로직 업데이트 및 렌더링
        # -----------------
        game.update()
        game.draw(visualized_frame)
        
        # 임시 플레이어 위치 시각화 (파란색 사각형)
        player_y = frame_height - 50 
        player_width = 80
        cv2.rectangle(visualized_frame, 
                      (int(player_x - player_width/2), player_y - 10), 
                      (int(player_x + player_width/2), player_y + 10), 
                      (255, 0, 0), -1) 
        
        # 입 벌림 상태 시각화
        status_text = "COLLECTING!" if is_mouth_open else "WAITING"
        color = (0, 0, 255) if is_mouth_open else (0, 255, 0)
        cv2.putText(visualized_frame, status_text, (frame_width - 200, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
        
        # C39: 입 벌림 비율 시각화 (디버깅용)
        dist_text = f"Mouth Ratio: {mouth_ratio:.3f}"
        cv2.putText(visualized_frame, dist_text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        
        # 최종 프레임 표시
        cv2.imshow('Christmas Game Filter', visualized_frame)

        # -----------------
        # 키 입력 처리 (Pause, Restart)
        # -----------------
        key = cv2.waitKey(5) & 0xFF
        
        if key == ord('q'):
            break
        
        # 'p' 키: 일시 정지/재개 토글
        if key == ord('p'):
            if not game.game_over:
                game.paused = not game.paused
        
        # 'r' 키: 게임 오버 상태일 때 재시작
        if key == ord('r') and game.game_over:
            game.reset_game()
        # -----------------

    # 자원 해제
    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()

if __name__ == "__main__":
    main()