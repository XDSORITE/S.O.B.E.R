import mediapipe as mp
import numpy as np
import cv2
import urllib.request
import os
import time

STATIC_IMAGE_MODE=False
MAX_NUM_FACES=1
MIN_DETECTION_CONFIDENCE=0.5
GAZE_THRESHOLD=0.65
GLANCE_COUNT=3
TIME_WINDOW=5

model_url= "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
if not os.path.exists("face_landmarker.task"):
    urllib.request.urlretrieve(model_url,"face_landmarker.task")

class GazeDetector:
    def __init__(self):
        BaseOptions=mp.tasks.BaseOptions
        FaceLandmarkerOptions=mp.tasks.vision.FaceLandmarkerOptions
        VisionRunningMode=mp.tasks.vision.RunningMode
        self.face_landmarker=mp.tasks.vision.FaceLandmarker.create_from_options(
            FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path='face_landmarker.task'),
                running_mode=VisionRunningMode.IMAGE,
                num_faces=MAX_NUM_FACES,
                min_face_detection_confidence=MIN_DETECTION_CONFIDENCE))
        self.lm=None

    def _vf(self,frame):
        if frame is None:
            return False
        if not isinstance(frame,np.ndarray):
            return False
        if len(frame.shape)!=3:
            return False
        if frame.shape[2] not in [3,4]:
            return False
        return True

    def _cfb(self,frame):
        if frame is None:
            return None
        if frame.dtype!=np.uint8:
            frame=np.clip(frame*255,0,255).astype(np.uint8)
        if len(frame.shape)==2:
            frame=cv2.cvtColor(frame,cv2.COLOR_GRAY2BGR)
        if frame.shape[2]==4:
            frame=cv2.cvtColor(frame,cv2.COLOR_BGRA2BGR)
        return frame

    def get_gaze_direction(self,landmarks,frame_h,frame_w):
        if not landmarks:
            return None
        if frame_h<=0 or frame_w<=0:
            return None
        try:
            left_iris=landmarks[468]
            right_iris=landmarks[473]
            left_eye_inner=landmarks[133]
            left_eye_outer=landmarks[33]
            right_eye_inner=landmarks[362]
            right_eye_outer=landmarks[263]
            left_eye_top=landmarks[159]
            left_eye_bottom=landmarks[145]
            right_eye_top=landmarks[386]
            right_eye_bottom=landmarks[374]
            left_gaze_x=(left_iris.x-left_eye_outer.x)/(left_eye_inner.x-left_eye_outer.x+1e-6)
            left_gaze_y=(left_iris.y-left_eye_top.y)/(left_eye_bottom.y-left_eye_top.y+1e-6)
            right_gaze_x=(right_iris.x-right_eye_outer.x)/(right_eye_inner.x-right_eye_outer.x+1e-6)
            right_gaze_y=(right_iris.y-right_eye_top.y)/(right_eye_bottom.y-right_eye_top.y+1e-6)
            left_gaze_x=np.clip(left_gaze_x,0,1)
            left_gaze_y=np.clip(left_gaze_y,0,1)
            right_gaze_x=np.clip(right_gaze_x,0,1)
            right_gaze_y=np.clip(right_gaze_y,0,1)
            avg_gaze_x=(left_gaze_x+right_gaze_x)/2.0
            avg_gaze_y=(left_gaze_y+right_gaze_y)/2.0
            return (float(avg_gaze_x),float(avg_gaze_y))
        except (IndexError,AttributeError,TypeError):
            return None

    def process(self,frame):
        if not self._vf(frame):
            return self.lm
        frame=self._cfb(frame)
        if frame is None:
            return self.lm
        try:
            mp_image=mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
            results=self.face_landmarker.detect(mp_image)
            if results.face_landmarks:
                landmarks=results.face_landmarks[0]
                self.lm=landmarks
                return landmarks
            return self.lm
        except Exception as e:
            return self.lm

class GlanceDetector:
    def __init__(self,gaze_threshold=GAZE_THRESHOLD,glance_count=GLANCE_COUNT,time_window=TIME_WINDOW):
        self.gaze_threshold=self.validate_threshold(gaze_threshold)
        self.glance_count=self.validate_glances(glance_count)
        self.time_window=time_window
        self.gd=0
        self.gt=[]
        self.lg=None

    def validate_threshold(self,t):
        if t is None:
            return 0.65
        try:
            t=float(t)
            if t<0.0:
                t=0.0
            if t>1.0:
                t=1.0
            return t
        except (ValueError,TypeError):
            return 0.65

    def validate_glances(self,g):
        if g is None:
            return 3
        try:
            g=int(g)
            if g<1:
                g=1
            if g>10:
                g=10
            return g
        except (ValueError,TypeError):
            return 3

    def _cgt(self,gd):
        if gd is None:
            return None
        if isinstance(gd,(list,tuple)):
            if len(gd)>=2:
                try:
                    return (float(gd[0]),float(gd[1]))
                except (ValueError,TypeError):
                    return None
        return None

    def _ld(self,gd):
        if gd is None:
            return False
        gd=self._cgt(gd)
        if gd is None:
            return False
        gx,gy=gd
        if gy<0.0 or gy>1.0:
            return False
        return gy>self.gaze_threshold

    def detect(self,gd,ct):
        gd=self._cgt(gd)
        self.lg=gd
        if self._ld(gd):
            self.gd+=1
            self.gt.append(ct)
        else:
            self.gd=0
        self.gt=[t for t in self.gt if ct-t<self.time_window]
        GA=len(self.gt)>=self.glance_count
        return GA

    def get_glance_count(self):
        return len(self.gt)

    def reset(self):
        self.gd=0
        self.gt=[]
        self.lg=None