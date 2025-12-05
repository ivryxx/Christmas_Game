import mediapipe as mp
import cv2
import numpy as np


MOUTH_UPPER = 10 
MOUTH_LOWER = 152 


# MediaPipe 객체 초기화
# mp_face_mesh: 468개 얼굴 랜드마크 검출
# mp_drawing: 랜드마크를 화면에 그릴 때 사용할 유틸리티
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Face Mesh 객체 생성 (static_image_mode=False: 실시간 비디오 처리 모드)
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,  # 눈, 입술 주변 랜드마크 세분화
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7)

def initialize_filter_system():
    """필터 시스템 초기화에 필요한 객체를 반환합니다."""
    return face_mesh, mp_drawing

def process_frame(frame, face_mesh_instance):
    """
    프레임을 받아 MediaPipe로 처리하고 결과를 반환합니다.
    (이 단계에서는 시각화 없이 순수 처리만 구현)
    """
    # BGR을 RGB로 변환 (MediaPipe 입력 형식)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # 프레임 처리
    results = face_mesh_instance.process(rgb_frame)
    
    # 처리된 프레임과 랜드마크 결과 반환
    return frame, results

# -----------------
# 랜드마크 분석 및 필터 렌더링 함수 

def calculate_mouth_dist(landmarks, frame_width, frame_height): 
    """
    입 벌림의 수직 거리(픽셀 단위)를 계산합니다.
    """
    if not landmarks:
        return 0

    # 📌 C22 수정: global 키워드를 사용하여 모듈 최상단 변수를 참조하도록 강제합니다.
    global MOUTH_UPPER, MOUTH_LOWER
    
    # 랜드마크 좌표 추출 (정규화된 [0.0, 1.0] 값을 픽셀 값으로 변환)
    # 이제 'global' 키워드 덕분에 'MOUTH_UPPER'를 직접 사용할 수 있습니다.
    upper_point = landmarks.landmark[MOUTH_UPPER] 
    lower_point = landmarks.landmark[MOUTH_LOWER]
    
    # 픽셀 좌표
    x1, y1 = int(upper_point.x * frame_width), int(upper_point.y * frame_height)
    x2, y2 = int(lower_point.x * frame_width), int(lower_point.y * frame_height)

    # 유클리디안 거리 계산 (numpy 사용)
    distance = np.linalg.norm(np.array([x1, y1]) - np.array([x2, y2]))
    
    return distance



def draw_filter(frame, landmarks):
    """필터(모자, 루돌프 코 등)를 그리는 함수 (C36~C40에서 구현 예정)"""
    # TODO: 이미지 합성 로직 구현
    pass


# Face Mesh 객체 생성 (기존 C5 내용)
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7)
    
# ... (기존 initialize_filter_system 및 process_frame 함수는 그대로 유지) ...

def draw_landmarks_and_mesh(frame, results, mp_drawing):
    """
    MediaPipe의 결과를 사용하여 랜드마크와 메쉬를 프레임에 시각화합니다.
    """
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # 1. 랜드마크를 연결하는 메쉬 그리기 (복잡도 때문에 주석 처리 가능)
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION, # 얼굴 외곽선 연결
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=1, circle_radius=1))
            
            # 2. 얼굴 윤곽선 (Contour) 그리기
            # mp_drawing.draw_landmarks(
            #     image=frame,
            #     landmark_list=face_landmarks,
            #     connections=mp_face_mesh.FACEMESH_CONTOURS, # 눈, 입, 코 등 윤곽선
            #     landmark_drawing_spec=None,
            #     connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=1))

    return frame