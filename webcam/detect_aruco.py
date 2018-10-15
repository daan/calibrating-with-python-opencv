import time
import numpy as np
import cv2

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)


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


camera = 0

cap = cv2.VideoCapture(camera)

color_frame = None
counter = 0

while(1):
    ret, frame = cap.read()
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