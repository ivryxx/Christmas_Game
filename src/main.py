import cv2

def main():
    # 0번 웹캠 장치 열기
    cap = cv2.VideoCapture(0)
    
    # 웹캠이 성공적으로 열렸는지 확인
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Webcam successfully opened. Press 'q' to exit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Ignoring empty camera frame.")
            break

        # 창 크기 조정 없이 원본 프레임 표시
        cv2.imshow('Christmas Game Filter (C4)', frame)

        # 'q' 키를 누르면 루프 종료
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    # 자원 해제
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()