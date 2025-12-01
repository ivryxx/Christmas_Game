import cv2
# filter_logic 모듈 import
import src.filter_logic as fl

def main():
    # 0번 웹캠 장치 열기
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # C5에서 작성된 MediaPipe Face Mesh 객체와 그리기 유틸리티를 초기화
    face_mesh, mp_drawing = fl.initialize_filter_system()
    
    print("Christmas Game Filter started. Press 'q' to exit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Ignoring empty camera frame.")
            continue
        
        # 좌우 반전: 셀카 모드처럼 보이게 하여 사용자 경험 개선
        frame = cv2.flip(frame, 1)

        # C5의 filter_logic 함수를 사용하여 프레임 처리
        # (이 단계에서는 랜드마크 시각화는 아직 filter_logic 내에서 하지 않음)
        processed_frame, results = fl.process_frame(frame, face_mesh)
        
        # 처리된 프레임 표시
        cv2.imshow('Christmas Game Filter (C6)', processed_frame)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    # MediaPipe 객체 해제 (선택 사항이나 권장됨)
    face_mesh.close()

if __name__ == "__main__":
    main()