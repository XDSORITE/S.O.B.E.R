import numpy
mouth=[61,39,0,269,287,405,17,181]
max_mouth_open = 0.6
yawning_for = 90 #in frames not seconds so its like 3.5 secounds
mouth_open_for = 0
mouth_closed_for = 0
yawn_timestamps=[]

#function names are there for a reason you dont need a comment
#just read it I am not explaining
def mouth_ratio_calculation(mouth_indices,all_the_landmarks,frame_width,frame_height):
    point0=(int(all_the_landmarks[mouth_indices[0]].x*frame_width),int(all_the_landmarks[mouth_indices[0]].y*frame_height))
    point1=(int(all_the_landmarks[mouth_indices[1]].x*frame_width),int(all_the_landmarks[mouth_indices[1]].y*frame_height))
    point2=(int(all_the_landmarks[mouth_indices[2]].x*frame_width),int(all_the_landmarks[mouth_indices[2]].y*frame_height))
    point3=(int(all_the_landmarks[mouth_indices[3]].x*frame_width),int(all_the_landmarks[mouth_indices[3]].y*frame_height))
    point4=(int(all_the_landmarks[mouth_indices[4]].x*frame_width),int(all_the_landmarks[mouth_indices[4]].y*frame_height))
    point5=(int(all_the_landmarks[mouth_indices[5]].x*frame_width),int(all_the_landmarks[mouth_indices[5]].y*frame_height))
    point6=(int(all_the_landmarks[mouth_indices[6]].x*frame_width),int(all_the_landmarks[mouth_indices[6]].y*frame_height))
    point7=(int(all_the_landmarks[mouth_indices[7]].x*frame_width),int(all_the_landmarks[mouth_indices[7]].y*frame_height))
    vertical_distance1=numpy.linalg.norm(numpy.array(point1)-numpy.array(point7))
    vertical_distance2=numpy.linalg.norm(numpy.array(point2)-numpy.array(point6))
    vertical_distance3=numpy.linalg.norm(numpy.array(point3)-numpy.array(point5))
    horizontal_distance=numpy.linalg.norm(numpy.array(point0)-numpy.array(point4))
    open_mouth_ratio=(vertical_distance1+vertical_distance2+vertical_distance3)/(3.0*horizontal_distance)
    return open_mouth_ratio

def yawning(mouth_score,current_time):
    global mouth_open_for,yawn_timestamps,mouth_closed_for
    if mouth_score > max_mouth_open:
        mouth_open_for=mouth_open_for + 1
        mouth_closed_for=0
    else:
        mouth_closed_for=mouth_closed_for + 1
        if mouth_closed_for > 5:
            if mouth_open_for >= yawning_for:
                yawn_timestamps.append(current_time)
            mouth_open_for = 0
    yawn_timestamps=[t for t in yawn_timestamps if current_time-t<60]
    too_many_yawns=len(yawn_timestamps) >= 2
    return too_many_yawns,len(yawn_timestamps)