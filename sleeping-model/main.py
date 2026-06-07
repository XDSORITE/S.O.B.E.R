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
from head_pose_detection import is_head_drooping
from sleepy_score import sleepy_score,get_alert_level

#this just downloads the model dont get worried buddy
model_url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
if not os.path.exists("face_landmarker.task"):
    urllib.request.urlretrieve(model_url, "face_landmarker.task")
sober_base_opts=python.BaseOptions(model_asset_path="face_landmarker.task")
sober_options=vision.FaceLandmarkerOptions(base_options=sober_base_opts, num_faces=1, min_face_detection_confidence=0.5, min_tracking_confidence=0.5)
sober_detector=vision.FaceLandmarker.create_from_options(sober_options)
driver_camera=cv2.VideoCapture(0)

while True:
    grabbed,driver_frame=driver_camera.read()
    if not grabbed:
        break
    driver_frame_h=driver_frame.shape[0]
    driver_frame_w=driver_frame.shape[1]
    rgb=cv2.cvtColor(driver_frame, cv2.COLOR_BGR2RGB)
    sober_result=sober_detector.detect(mediapipe.Image(image_format=mediapipe.ImageFormat.SRGB, data=rgb))
    if sober_result.face_landmarks:
        driver_landmarks=sober_result.face_landmarks[0]
        for dot in driver_landmarks:
            cv2.circle(driver_frame, (int(dot.x*driver_frame_w), int(dot.y*driver_frame_h)), 1, (0,255,0), -1)
        eyes_closed,both_eyes_average_ear=eye_closed_check(driver_landmarks,driver_frame_w,driver_frame_h)
        mouth_open_ratio=mouth_ratio_calculation(mouth,driver_landmarks,driver_frame_w,driver_frame_h)
        too_many_yawns,yawn_count=yawning(mouth_open_ratio,time.time())
        head_is_drooping,pitch=is_head_drooping(driver_landmarks,driver_frame_w,driver_frame_h)
        total_sleepy_score=sleepy_score(both_eyes_average_ear,head_is_drooping,yawn_count)
        current_alert=get_alert_level(total_sleepy_score,time.time())
        cv2.putText(driver_frame, f"ear: {both_eyes_average_ear:.2f}", (30,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.putText(driver_frame, f"pitch: {pitch:.2f}", (30,55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.putText(driver_frame, f"sleepy score: {total_sleepy_score}", (30,80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.putText(driver_frame, f"yawns: {yawn_count}", (30,105), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.putText(driver_frame, f"mar: {mouth_open_ratio:.2f}", (30,130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        if current_alert == "attention":
            cv2.putText(driver_frame, "stay alert!!", (30,140), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,165,255), 3)
        if current_alert == "alarm":
            cv2.putText(driver_frame, "WAKE UP!!", (30,180), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,0,255), 4)
    cv2.imshow("S.O.B.E.R", driver_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
driver_camera.release()