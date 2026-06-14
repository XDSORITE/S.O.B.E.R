import cv2
import numpy as np
import time
from glance_detection import GazeDetector,GlanceDetector

GAZE_THRESHOLD=0.65
GLANCE_COUNT=3
TIME_WINDOW=5
MAX_HISTORY=100

class SOBERDetector:
    def __init__(self,gaze_threshold=GAZE_THRESHOLD,glance_count=GLANCE_COUNT,time_window=TIME_WINDOW):
        self.gaze_detector=GazeDetector()
        self.glance_detector=GlanceDetector(
            gaze_threshold=gaze_threshold,
            glance_count=glance_count,
            time_window=time_window)
        self.fc=0
        self.dh=[]
        self.st=time.time()

    def _vvp(self,vp):
        if vp is None:
            return False
        if not isinstance(vp,str):
            return False
        return True

    def process_frame(self,frame):
        if frame is None:
            return None
        if not isinstance(frame,np.ndarray):
            return None
        h,w=frame.shape[:2]
        if h<=0 or w<=0:
            return None
        lm=self.gaze_detector.process(frame)
        gaze=None
        ga=False
        gc=0
        if lm:
            gaze=self.gaze_detector.get_gaze_direction(lm,h,w)
            ct=time.time()-self.st
            ga=self.glance_detector.detect(gaze,ct)
            gc=self.glance_detector.get_glance_count()
        result={
            "gaze":gaze,
            "glance_alert":ga,
            "glance_count":gc,
            "landmarks":lm,
            "frame_number":self.fc
        }
        self.dh.append(result)
        if len(self.dh)>MAX_HISTORY:
            self.dh.pop(0)
        return result

    def _dgp(self,frame,gaze):
        if frame is None or gaze is None:
            return frame
        if not isinstance(gaze,(tuple,list)):
            return frame
        if len(gaze)<2:
            return frame
        try:
            h,w=frame.shape[:2]
            gx=float(gaze[0])
            gy=float(gaze[1])
            x=int(gx*w)
            y=int(gy*h)
            if 0<=x<w and 0<=y<h:
                cv2.circle(frame,(x,y),5,(0,255,0),-1)
        except (ValueError,TypeError,IndexError):
            pass
        return frame

    def _dga(self,frame,detected,count):
        if frame is None:
            return frame
        if not detected:
            return frame
        try:
            text=f"GLANCE ALERT ({count})"
            cv2.putText(frame,text,(10,30),
                       cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)
        except Exception:
            pass
        return frame

    def run_video(self,video_path):
        if not self._vvp(video_path):
            return False
        try:
            driver_camera=cv2.VideoCapture(0)
            if not driver_camera.isOpened():
                print("Error: Could not open camera.")
                return False
            while True:
                grabbed,driver_frame=driver_camera.read()
                if not grabbed:
                    print("Error: Can't receive frame.")
                    break
                self.fc+=1
                result=self.process_frame(driver_frame)
                if result is None:
                    continue
                driver_frame=self._dgp(driver_frame,result["gaze"])
                driver_frame=self._dga(driver_frame,result["glance_alert"],result["glance_count"])
                cv2.imshow("SOBER",driver_frame)
                if cv2.waitKey(1)&0xFF==ord('q'):
                    break
            driver_camera.release()
            cv2.destroyAllWindows()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def run_webcam(self,camera_id=0):
        return self.run_video(camera_id)

    def get_detection_stats(self):
        if not self.dh:
            return None
        total=len(self.dh)
        alerts=sum(1 for d in self.dh if d["glance_alert"])
        max_glances=max((d["glance_count"] for d in self.dh),default=0)
        return {
            "total_frames":total,
            "alerts":alerts,
            "alert_rate":alerts/total,
            "max_glances":max_glances
        }

if __name__=="__main__":
    print("Starting webcam...")
    detector=SOBERDetector()
    result=detector.run_webcam(0)
    print(f"Result: {result}")