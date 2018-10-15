from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime

import time
import numpy as np
import cv2

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)

color_image_size = (1080,1920)
color_image_shape = (1080,1920,4)

def detect_aruco_markers(img, dictionary):
    corner_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.00001)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, dictionary) 
    if len(corners)>0:
        for corner in corners:
            cv2.cornerSubPix(gray, corner, winSize=(3,3), zeroZone=(-1,-1), criteria=corner_criteria)        
        ret, detectedCorners, detectedIds = cv2.aruco.interpolateCornersCharuco(corners,ids,gray,board)
        if detectedCorners is not None and detectedIds is not None and len(detectedCorners)>3:
             return detectedCorners, detectedIds
    return [], []    


kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color)

color_frame = None
counter = 0

while(1):
    if kinect.has_new_color_frame():
        color_frame = kinect.get_last_color_frame()
        color_frame = color_frame.reshape(color_image_shape)

        color_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGRA2BGR)
        color_flipped = cv2.flip(color_frame,1)

        corners, ids = find_aruco_markers(color_flipped, board, dictionary)

        if len(corners) > 0:
            cv2.aruco.drawDetectedMarkers(color_flipped, corners, ids)
        cv2.imshow('color',color_flipped)
    
    key = cv2.waitKey(1)
    if key == 27:
        cv2.destroyAllWindows()
        kinect.close()
        break
    elif key == 32:
        if color_frame != None:
            cv2.imwrtie("frame_{}.jpg".format(counter), cv2.flip(color_frame,1))
            counter += 1