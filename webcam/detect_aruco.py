import time
import numpy as np
import cv2

from shared import *

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)



camera = 0

cap = cv2.VideoCapture(camera)

color_frame = None
counter = 0

while(1):
    ret, frame = cap.read()

    corners, ids = detect_aruco_markers(frame, dictionary)

    if len(corners) > 0:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
    cv2.imshow('color', frame)
    
    key = cv2.waitKey(1)
    if key == 27:
        cv2.destroyAllWindows()
        kinect.close()
        break
    elif key == 32:
        if color_frame != None:
            cv2.imwrtie("frame_{}.jpg".format(counter), cv2.flip(color_frame,1))
            counter += 1