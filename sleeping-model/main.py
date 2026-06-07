# dont ask how it works took me way to long to figure it out
# but it just does
# I promise :)

import cv2
import mediapipe
import urllib.request
import os
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from sleepy_eyes_detection import eye_closed_check
from yawning_detection import yawning,mouth_ratio_calculation,mouth

#this just downloads the model dont get worried buddy
model_url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
if not os.path.exists("face_landmarker.task"):
    urllib.request.urlretrieve(model_url, "face_landmarker.task")
sober_base_opts = python.BaseOptions(model_asset_path="face_landmarker.task")
sober_options = vision.FaceLandmarkerOptions(base_options=sober_base_opts, num_faces=1, min_face_detection_confidence=0.5, min_tracking_confidence=0.5)
sober_detector = vision.FaceLandmarker.create_from_options(sober_options)
driver_camera = cv2.VideoCapture(0)

while True:
    grabbed,driver_frame= driver_camera.read()
    if not grabbed:
        break
    driver_frame_h = driver_frame.shape[0]
    driver_frame_w = driver_frame.shape[1]
    rgb = cv2.cvtColor(driver_frame, cv2.COLOR_BGR2RGB)
    sober_result = sober_detector.detect(mediapipe.Image(image_format=mediapipe.ImageFormat.SRGB, data=rgb))
    if sober_result.face_landmarks:
        driver_landmarks = sober_result.face_landmarks[0]
        for dot in driver_landmarks:
            cv2.circle(driver_frame, (int(dot.x*driver_frame_w), int(dot.y * driver_frame_h)), 1, (0, 255, 0), -1)
        eyes_closed,ear=eye_closed_check(driver_landmarks,driver_frame_w,driver_frame_h)
        mar=mouth_ratio_calculation(mouth, driver_landmarks,driver_frame_w,driver_frame_h)
        too_many_yawns,yawn_count=yawning(mar,time.time())
        if eyes_closed:
            cv2.putText(driver_frame, "hey wake up!!", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        if too_many_yawns:
            cv2.putText(driver_frame, "stop yawning!!", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            yawn_count=0
        cv2.putText(driver_frame, f"ear: {ear:.2f}", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(driver_frame, f"yawns: {yawn_count}", (30, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(driver_frame, f"mar: {mar:.2f}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.imshow("S.O.B.E.R", driver_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
driver_camera.release()