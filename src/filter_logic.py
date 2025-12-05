import cv2
import mediapipe as mp
import numpy as np

# MediaPipe 객체 초기화
mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh

# 입 벌림 거리 측정을 위한 랜드마크 인덱스 정의
MOUTH_UPPER = 10 
MOUTH_LOWER = 152 

# 머리 자세 추정(Head Pose Estimation)을 위한 랜드마크 인덱스 정의
HEAD_POSE_LANDMARKS = [
    33,   # 왼쪽 눈 (Outer Corner)
    263,  # 오른쪽 눈 (Outer Corner)
    1,    # 코 끝 (Nose Tip)
    61,   # 왼쪽 입가 (Left Mouth Corner)
    291,  # 오른쪽 입가 (Right Mouth Corner)
    199   # 턱 끝 (Chin Center)
]


# PnP 알고리즘을 위한 3D 모델
MODEL_3D_POINTS = np.array([
    (-225.0, 170.0, -135.0),
    (225.0, 170.0, -135.0),
    (0.0, 0.0, 0.0),
    (-150.0, -150.0, -125.0),
    (150.0, -150.0, -125.0),
    (0.0, -330.0, -65.0)
], dtype=np.float32)

def initialize_filter_system():
    """MediaPipe Face Mesh 객체를 초기화하고 반환합니다."""
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)
    return face_mesh, mp_drawing

def process_frame(frame, face_mesh):
    """MediaPipe Face Mesh를 사용하여 프레임을 처리합니다."""
    frame.flags.writeable = False
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame)
    frame.flags.writeable = True
    processed_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return processed_frame, results

def draw_landmarks_and_mesh(frame, results, mp_drawing):
    """얼굴 메쉬와 랜드마크를 그립니다."""
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(120, 120, 120), thickness=1, circle_radius=1))
    return frame

def calculate_mouth_dist(landmarks, frame_width, frame_height): 
    """입 벌림의 수직 거리(픽셀 단위)를 계산합니다."""
    if not landmarks:
        return 0

    # global 키워드를 사용하여 모듈 최상단 변수를 참조
    global MOUTH_UPPER, MOUTH_LOWER 
    
    # 랜드마크 좌표 추출
    upper_point = landmarks.landmark[MOUTH_UPPER] 
    lower_point = landmarks.landmark[MOUTH_LOWER]
    
    # 픽셀 좌표
    x1, y1 = int(upper_point.x * frame_width), int(upper_point.y * frame_height)
    x2, y2 = int(lower_point.x * frame_width), int(lower_point.y * frame_height)

    # 유클리디안 거리 계산
    distance = np.linalg.norm(np.array([x1, y1]) - np.array([x2, y2]))
    
    return distance

def get_head_pose(landmarks, frame_width, frame_height):
    """
    얼굴 랜드마크를 사용하여 머리의 회전 벡터를 추정합니다 (PnP).
    """
    if not landmarks:
        return None, None, None, None

    image_points = np.zeros((6, 2), dtype=np.float32)
    for i, idx in enumerate(HEAD_POSE_LANDMARKS):
        point = landmarks.landmark[idx]
        x = point.x * frame_width
        y = point.y * frame_height
        image_points[i] = [x, y]

    focal_length = frame_width
    center = (frame_width / 2, frame_height / 2)
    
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype=np.float32)

    dist_coeffs = np.zeros((4, 1), dtype=np.float32)

    (success, rotation_vector, translation_vector) = cv2.solvePnP(
        MODEL_3D_POINTS, image_points, camera_matrix, dist_coeffs, 
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    return rotation_vector, image_points, camera_matrix, dist_coeffs
def draw_head_pose_axis(frame, rvec, image_points, camera_matrix, dist_coeffs):
    """머리 자세(Head Pose)의 3D 축을 프레임에 시각화합니다."""
    if rvec is None:
        return frame

    axis = np.float32([[100, 0, 0], [0, 100, 0], [0, 0, 100]]).reshape(-1, 3)

    (imgpts, jac) = cv2.projectPoints(axis, rvec, np.zeros((3, 1)), camera_matrix, dist_coeffs)
    
    nose_tip = tuple(image_points[2].ravel().astype(int))

    frame = cv2.line(frame, nose_tip, tuple(imgpts[0].ravel().astype(int)), (0, 0, 255), 3) # X (빨강)
    frame = cv2.line(frame, nose_tip, tuple(imgpts[1].ravel().astype(int)), (0, 255, 0), 3) # Y (초록)
    frame = cv2.line(frame, nose_tip, tuple(imgpts[2].ravel().astype(int)), (255, 0, 0), 3) # Z (파랑)
    
    return frame