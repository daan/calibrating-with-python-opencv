import glob
import numpy as np
import cv2
from cv2 import aruco

import json
import argparse

def find_charuco_board(img, board, dictionary):
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



squareLength = 35.0 / 1000 # chessboard square side length (normally in meters)
markerLength = 22.0 / 1000 # marker side length (same unit than squareLength)
squaresX = 5
squaresY = 7

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
board = cv2.aruco.CharucoBoard_create(squaresX,squaresY,squareLength,markerLength,dictionary)

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", help="path to output folder")
ap.add_argument("-c", "--camera", type=int, default=0, help="camera by id")

# read calibration file
fs = cv2.FileStorage("calibration.json", cv2.FILE_STORAGE_READ)
intrinsics = fs.getNode("cameraMatrix").mat()
dist_coeffs = fs.getNode("dist_coeffs").mat()

print(" xxx  ",intrinsics, dist_coeffs)

args = vars(ap.parse_args())
camera = args["camera"]

print("opening video capture device {}".format(camera))
cap = cv2.VideoCapture(int(camera))
print("resolution {} by {} ".format(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT ))))



while(True):
    if cv2.waitKey(1) == 27: # ESC
        cv2.destroyAllWindows()
        break

    ret, frame = cap.read()
    corners, ids = find_charuco_board(frame, board, dictionary)
    if len(corners) > 0 :
        valid, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(corners, ids, board, intrinsics, dist_coeffs)
        print(tvec)
    
        cv2.aruco.drawAxis(frame, intrinsics, dist_coeffs, rvec, tvec, 0.2) 


    ##if len(corners) > 0:
    #    cv2.aruco.drawDetectedCornersCharuco(frame, corners, ids)

    cv2.imshow('frame', frame)




