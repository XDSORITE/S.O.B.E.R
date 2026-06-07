import numpy
R_EYE=[33,160,158,133,153,144]
L_EYE=[362,385,387,263,373,380]
blink_cutoff=0.2
sleepy_after=50
shut_for=0

#function names are there for a reason you dont need a comment
#just read it I am not explaining
def eye_ratio_calcilation(which_eye_indices,all_the_landmarks,frame_width,frame_height):
    point0=(int(all_the_landmarks[which_eye_indices[0]].x*frame_width), int(all_the_landmarks[which_eye_indices[0]].y*frame_height))
    point1=(int(all_the_landmarks[which_eye_indices[1]].x*frame_width), int(all_the_landmarks[which_eye_indices[1]].y*frame_height))
    point2=(int(all_the_landmarks[which_eye_indices[2]].x*frame_width), int(all_the_landmarks[which_eye_indices[2]].y*frame_height))
    point3=(int(all_the_landmarks[which_eye_indices[3]].x*frame_width), int(all_the_landmarks[which_eye_indices[3]].y*frame_height))
    point4=(int(all_the_landmarks[which_eye_indices[4]].x*frame_width), int(all_the_landmarks[which_eye_indices[4]].y*frame_height))
    point5=(int(all_the_landmarks[which_eye_indices[5]].x*frame_width), int(all_the_landmarks[which_eye_indices[5]].y*frame_height))
    vertical_distance1=numpy.linalg.norm(numpy.array(point1)-numpy.array(point5))
    vertical_distance2=numpy.linalg.norm(numpy.array(point2)-numpy.array(point4))
    horizontal_distnace=numpy.linalg.norm(numpy.array(point0)-numpy.array(point3))
    the_ear_value=(vertical_distance1+vertical_distance2)/(2.0*horizontal_distnace)
    return the_ear_value

def eye_closed_check(found_landmarks,frame_width,frame_height):
    global shut_for
    left_eye_score=eye_ratio_calcilation(L_EYE,found_landmarks,frame_width,frame_height)
    right_eye_score=eye_ratio_calcilation(R_EYE,found_landmarks,frame_width,frame_height)
    both_eye_score=(left_eye_score+right_eye_score)/2.0
    if left_eye_score < blink_cutoff and right_eye_score < blink_cutoff:
        shut_for=shut_for+1
    else:
        shut_for=0
    return shut_for >= sleepy_after,both_eye_score