import time

eye_detection_weight=40
yawn_detection_weight=25
head_pose_detection_weight=35
attention_threshold= 40
alarm_threshold=70
last_alarm_time=0
last_attention_time=0

def sleepy_score(both_eyes_average_ear,head_is_drooping,yawn_count):
    eye_open_score=max(0, min(100, (1-both_eyes_average_ear/0.28)*100))
    if head_is_drooping:
        head_drooping_score = 100
    else:
        head_drooping_score =0
    if yawn_count==0:
        yawn_frequency_score=0
    elif yawn_count == 1:
        yawn_frequency_score=50
    else:
        yawn_frequency_score=100
    total_sleepy_score=(eye_open_score* eye_detection_weight/100)+(head_drooping_score*head_pose_detection_weight/100)+(yawn_frequency_score*yawn_detection_weight/100)
    return int(total_sleepy_score)

def get_alert_level(total_sleepy_score,current_time):
    global last_alarm_time,last_attention_time
    if total_sleepy_score >= alarm_threshold:
        if current_time-last_alarm_time >= 3:
            last_alarm_time=current_time
            return "alarm"
    elif total_sleepy_score>= attention_threshold:
        if current_time-last_attention_time >= 8:
            last_attention_time =current_time
            return "attention"
    return "none"