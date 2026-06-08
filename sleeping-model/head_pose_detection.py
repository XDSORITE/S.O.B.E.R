import cv2
import numpy

HEAD_POSE_LANDMARKS = [4,152,234,454,33,263]

face_3d_model_points = numpy.array([
    (0.0, 0.0, 0.0),
    (0.0, -330.0, -65.0),
    (-225.0, 170.0, -135.0),
    (225.0, 170.0, -135.0),
    (-150.0, -150.0, -125.0),
    (150.0, -150.0, -125.0)
], dtype=numpy.float64)

head_pitch_threshold = -15
head_drooping = False

def get_head_pitch(found_landmarks,frame_width,frame_height):
    image_2d_points = numpy.array([
        (found_landmarks[4].x * frame_width,   found_landmarks[4].y * frame_height),
        (found_landmarks[152].x * frame_width, found_landmarks[152].y * frame_height),
        (found_landmarks[234].x * frame_width, found_landmarks[234].y * frame_height),
        (found_landmarks[454].x * frame_width, found_landmarks[454].y * frame_height),
        (found_landmarks[33].x * frame_width,  found_landmarks[33].y * frame_height),
        (found_landmarks[263].x * frame_width, found_landmarks[263].y * frame_height)
    ], dtype=numpy.float64)
    focal_length=frame_width
    camera_center=(frame_width/2, frame_height/2)
    camera_matrix=numpy.array([
        [focal_length, 0, camera_center[0]],
        [0, focal_length, camera_center[1]],
        [0, 0, 1]
    ], dtype=numpy.float64)
    dist_coeffs=numpy.zeros((4,1))
    success,rotation_vector,translation_vector=cv2.solvePnP(face_3d_model_points,image_2d_points,camera_matrix,dist_coeffs)
    rotation_matrix,_=cv2.Rodrigues(rotation_vector)
    angles,_,_,_,_,_=cv2.RQDecomp3x3(rotation_matrix)
    pitch=angles[0]
    return pitch

def is_head_drooping(found_landmarks,frame_width,frame_height):
    global head_drooping
    pitch=get_head_pitch(found_landmarks,frame_width,frame_height)
    head_drooping=pitch < head_pitch_threshold
    return head_drooping,pitch