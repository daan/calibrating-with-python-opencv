#
#	shared code between samples
#

import numpy as np
import cv2
def detect_aruco_markers(img, dictionary):
    corner_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.00001)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, dictionary) 
    if len(corners)>0:
        for corner in corners:
            cv2.cornerSubPix(gray, corner, winSize=(3,3), zeroZone=(-1,-1), criteria=corner_criteria)        
    return corners, ids
