import cv2
import filter_logic as fl # 'src.' 제거 확인

def main():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # 📌 필수: Face Mesh 객체와 그리기 유틸리티를 초기화하고 변수에 할당합니다.
    face_mesh, mp_drawing = fl.initialize_filter_system()
    
    print("Christmas Game Filter started. Press 'q' to exit.")
    
    # 프레임 크기 미리 가져오기
    # cap이 열린 후에 실행되어야 합니다.
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Ignoring empty camera frame.")
            continue
        
        frame = cv2.flip(frame, 1) # 좌우 반전

        # face_mesh를 인자로 전달하여 처리 (오류 해결 지점)
        processed_frame, results = fl.process_frame(frame, face_mesh)
        
        mouth_dist = 0
        
        # 랜드마크 분석 및 거리 계산
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            # C10 함수 호출 시 frame_width, frame_height 인자 전달
            mouth_dist = fl.calculate_mouth_dist(landmarks, frame_width, frame_height)


            
            
            # 랜드마크 시각화
            visualized_frame = fl.draw_landmarks_and_mesh(processed_frame, results, mp_drawing)
        else:
            # 얼굴을 찾지 못했다면 기존 프레임 사용
            visualized_frame = processed_frame 
            
        # -----------------
        # C11: 입 벌림 거리 시각화
        # -----------------
        display_text = f"Mouth Dist: {mouth_dist:.2f} px"
        # 랜드마크를 그린 프레임에 텍스트를 추가합니다.
        cv2.putText(visualized_frame, display_text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        
        cv2.imshow('Christmas Game Filter (C13)', visualized_frame)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break




        

    # 📌 필수: 자원 해제
    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close() # face_mesh가 정의되어 있어야 실행됨

if __name__ == "__main__":
    main()