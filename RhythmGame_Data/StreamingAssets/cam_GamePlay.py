import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')
import cv2
import mediapipe as mp
import pyautogui
import socket
import struct
import time

# 키 설정
keys = ['D', 'F', 'J', 'K']
current_keys = set()

def create_keyboxes():
    gap = 20
    box_size = 465
    positions = []
    for i, key in enumerate(keys):
        x = i * (box_size + gap)
        y = 30
        positions.append({'key': key, 'pos': (x, y), 'size': box_size})
    return positions

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

host = '127.0.0.1'
port = 12345
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"✅ 포트 {port} 바인딩 성공, 서버 대기 중...")
except Exception as e:
    print(f"❌ 바인딩 실패: {e}")
    exit(1)

time.sleep(1.0)  # Unity 소켓 준비될 때까지 대기

try:
    client_socket, client_addr = server_socket.accept()
    print("클라이언트 연결됨:", client_addr)
except Exception as e:
    print("❌ 클라이언트 연결 실패:", e)
    exit(1)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    crop_top = h // 4
    crop_bottom = crop_top + h // 2
    frame = frame[crop_top:crop_bottom, :]

    key_boxes = create_keyboxes()
    pressed_keys = set()

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            for lm in hand_landmarks.landmark:
                cx = int(lm.x * w)
                cy = int(lm.y * (crop_bottom - crop_top))
                for box in key_boxes:
                    x, y = box['pos']
                    size = box['size']
                    if x <= cx <= x + size and y <= cy <= y + size:
                        pressed_keys.add(box['key'])

    for key in pressed_keys - current_keys:
        pyautogui.keyDown(key.lower())
    for key in current_keys - pressed_keys:
        pyautogui.keyUp(key.lower())
    current_keys = pressed_keys

    for box in key_boxes:
        x, y = box['pos']
        size = box['size']
        if box['key'] in current_keys:
            overlay = frame.copy()
            cv2.rectangle(overlay, (x, y), (x + size, y + size), (56, 139, 221), -1)
            frame = cv2.addWeighted(overlay, 0.4, frame, 0.6, 0)
        else:
            cv2.rectangle(frame, (x, y), (x + size, y + size), (255, 255, 255), 2)

    encoded, buffer = cv2.imencode(".png", frame)
    if not encoded:
        continue
    data = buffer.tobytes()
    message_size = struct.pack("L", len(data))
    try:
        client_socket.sendall(message_size + data)
    except:
        print("클라이언트 연결 끊김")
        break

cap.release()
client_socket.close()
server_socket.close()