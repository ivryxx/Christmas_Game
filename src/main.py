import cv2
import src.filter_logic as fl

def main():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # MediaPipe 객체와 그리기 유틸리티 초기화
    face_mesh, mp_drawing = fl.initialize_filter_system()
    
    print("Christmas Game Filter started. Press 'q' to exit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Ignoring empty camera frame.")
            continue
        
        frame = cv2.flip(frame, 1)

        # 1. MediaPipe 처리
        # processed_frame은 frame과 동일하나, 관례상 이름 유지
        processed_frame, results = fl.process_frame(frame, face_mesh)
        
        # 2. 랜드마크 시각화 적용 (C7에서 추가된 함수 사용)
        visualized_frame = fl.draw_landmarks_and_mesh(processed_frame, results, mp_drawing)
        
        # 최종 프레임 표시
        cv2.imshow('Christmas Game Filter (C8)', visualized_frame)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()

if __name__ == "__main__":
    main()