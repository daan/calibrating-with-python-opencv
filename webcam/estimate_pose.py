import glob
import numpy as np
import cv2
from cv2 import aruco
import sys

import json
import argparse

def find_charuco_board(img, board, dictionary):
    corner_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.00001)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, dictionary) 
    if corners is None or ids is None:
        return [], []
    
    if len(corners)>0:
        for corner in corners:
            cv2.cornerSubPix(gray, corner, winSize=(3,3), zeroZone=(-1,-1), criteria=corner_criteria)        
        ret, detectedCorners, detectedIds = cv2.aruco.interpolateCornersCharuco(corners,ids,gray,board)
        print("ret", ret)
        if detectedCorners is None or detectedIds is None:
            return [], []
        if len(detectedCorners) < 3:
            return [], []

        if len(detectedCorners) != len(detectedIds):
            print("numver of corners != ids")
            return [],[]
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
fs = cv2.FileStorage("sample-data/calibration.json", cv2.FILE_STORAGE_READ)
if fs.isOpened() == False:
    print("couldn't load calibration data")
    sys.exit()

intrinsics = fs.getNode("cameraMatrix").mat()
dist_coeffs = fs.getNode("dist_coeffs").mat()
print("intriniscs", intrinsics)
print("dist coeffs", dist_coeffs)

args = vars(ap.parse_args())
camera = args["camera"]

print("opening video capture device {}".format(camera))
cap = cv2.VideoCapture(int(camera))
print("resolution {} by {} ".format(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT ))))


count = 0
tvecs = []
font = cv2.FONT_HERSHEY_SIMPLEX

while(True):
    ret, frame = cap.read()
    got_board = False
    corners, ids = find_charuco_board(frame, board, dictionary)
    if len(corners) > 0 :
        valid, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(corners, ids, board, intrinsics, dist_coeffs)
        if valid == True:
            org_frame = np.copy(frame)
            cv2.aruco.drawAxis(frame, intrinsics, dist_coeffs, rvec, tvec, 0.2)        
            got_board = True
            p3d = [tvec[0][0], tvec[1][0], tvec[2][0]]

            # draw the coordinates
            cv2.putText(frame,"{0:.3f}".format(p3d[0]), (100,200), font, 4,(0,0,255), 6, cv2.LINE_AA)
            cv2.putText(frame,"{0:.3f}".format(p3d[1]), (100,400), font, 4,(0,255,0), 6, cv2.LINE_AA)
            cv2.putText(frame,"{0:.3f}".format(p3d[2]), (100,600), font, 4,(255,0,0), 6, cv2.LINE_AA)


    key = cv2.waitKey(1)
    if key == 27: # ESC
        cv2.destroyAllWindows()
        break

    cv2.imshow('frame', frame)




