import cv2

# 웹캠 열기
cap = cv2.VideoCapture(1)

# 웹캠이 제대로 열렸는지 확인
if not cap.isOpened():
    print("웹캠을 열 수 없습니다!")
    exit()

while True:
    # 프레임 캡처
    ret, frame = cap.read()
    
    # 프레임이 정상적으로 캡처되었는지 확인
    if not ret:
        print("프레임 캡처 실패!")
        break

    # 프레임 화면에 표시
    cv2.imshow("Webcam Feed", frame)

    # 'q' 키를 눌러 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 웹캠 리소스 해제
cap.release()
cv2.destroyAllWindows()
