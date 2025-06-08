import cv2
import mediapipe as mp
import pyautogui
import socket
import struct
import math

# 거리 계산 함수
def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

# Mediapipe 설정
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# 카메라 설정
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# 소켓 연결 (Unity용 영상 전송)
host = '127.0.0.1'
port = 12346
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(1)
print("서버 대기 중...")
client_socket, client_addr = server_socket.accept()
print("클라이언트 연결됨:", client_addr)

# 이전 상태 저장
prev_left = False
prev_right = False
prev_enter = False

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    crop_top = h // 4
    crop_bottom = crop_top + h // 2
    frame = frame[crop_top:crop_bottom, :]

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)

    left_fist = False
    right_fist = False
    ok_sign = False

    if result.multi_hand_landmarks and result.multi_handedness:
        for hand, hand_type in zip(result.multi_hand_landmarks, result.multi_handedness):
            label = hand_type.classification[0].label  # 'Left' 또는 'Right'

            # 주먹 판정
            folded = 0
            for tip in [8, 12, 16, 20]:
                if hand.landmark[tip].y > hand.landmark[tip - 2].y:
                    folded += 1

            # Mediapipe는 좌우 반대로 인식됨 (거울 모드)
            if folded >= 3:
                if label == 'Right':
                    left_fist = True
                elif label == 'Left':
                    right_fist = True

            # 오케이 사인 판정 (검지 + 엄지 가까움)
            thumb_tip = hand.landmark[4]
            index_tip = hand.landmark[8]
            dist = distance(thumb_tip, index_tip)

            if dist < 0.05:
                ok_sign = True

            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

    # ✅ 입력 처리
    if ok_sign:
        if not prev_enter:
            pyautogui.keyDown('enter')
            prev_enter = True
        if prev_left:
            pyautogui.keyUp('a')
            prev_left = False
        if prev_right:
            pyautogui.keyUp('d')
            prev_right = False
    else:
        if prev_enter:
            pyautogui.keyUp('enter')
            prev_enter = False

        # 오른손만 주먹 → D
        if right_fist and not prev_right:
            pyautogui.keyDown('d')
            prev_right = True
        if not right_fist and prev_right:
            pyautogui.keyUp('d')
            prev_right = False

        # 왼손만 주먹 → A
        if left_fist and not prev_left:
            pyautogui.keyDown('a')
            prev_left = True
        if not left_fist and prev_left:
            pyautogui.keyUp('a')
            prev_left = False

    # Unity로 영상 전송
    encoded, buffer = cv2.imencode(".png", frame)
    if not encoded:
        continue
    data = buffer.tobytes()
    msg_size = struct.pack("L", len(data))
    try:
        client_socket.sendall(msg_size + data)
    except:
        print("클라이언트 연결 끊김")
        break

cap.release()
client_socket.close()
server_socket.close()
