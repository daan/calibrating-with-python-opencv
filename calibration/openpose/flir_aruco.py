import sys
import time
import PySpin
import os

import numpy as np
import cv2

import argparse


charuco_square_length = 140.0 / 1000 # chessboard square side length (normally in meters)
charuco_marker_length = 88.0 / 1000 # marker side length (same unit than squareLength)
squaresX = 5
squaresY = 7
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
board = cv2.aruco.CharucoBoard_create(squaresX,squaresY,charuco_square_length,charuco_marker_length,dictionary)



filename = "models/18284509.xml"

fs = cv2.FileStorage(filename, cv2.FILE_STORAGE_READ)

intrinsics = fs.getNode("Intrinsics").mat()
dist_coeffs = fs.getNode("Distortion").mat()

fs.release()



# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--camera", type=str, default="0", help="camera by id")

args = vars(ap.parse_args())

def set_trigger_mode_software(cam):
    cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
    cam.TriggerSource.SetValue(PySpin.TriggerSource_Software)
    cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
    print("set trigger mode software")


def reset_trigger_mode_software(cam):
    cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
    print("reset trigger mode")



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
        





#
#   setup
#

system = PySpin.System.GetInstance()
cam_list = system.GetCameras()

if cam_list.GetSize() == 0:
    print("no cameras found, aborting")
    system.ReleaseInstance()
    del system
    sys.exit()

cameras = []
for i in range(cam_list.GetSize()):
    cam = cam_list.GetByIndex(i)
    print("camera {} serial: {}".format(i, cam.GetUniqueID()))


camera_serial = args["camera"]
if camera_serial == "0":
    camera_serial = cam_list.GetByIndex(0).GetUniqueID()
    print("no camera specified (use -c), using the first one in the list {}".format(camera_serial))


cam = cam_list.GetBySerial(camera_serial)

try:
    cam.Init()
    cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
    set_trigger_mode_software(cam)
    cam.BeginAcquisition()

except:
    print("error initializing camera {}".format(camera_serial))
    sys.exit()


#os.mkdir(camera_serial)



#
#   loop
#

count = 0

while 1:
    key = cv2.waitKey(1)



    if key == 27: # ESC
        cv2.destroyAllWindows()
        break
    
    cam.TriggerSoftware()
    i = cam.GetNextImage()
        #print(i.GetWidth(), i.GetHeight(), i.GetBitsPerPixel())
    frame = None 

    font = cv2.FONT_HERSHEY_SIMPLEX

    if i.IsIncomplete():
        pass
    else:            
        # see documentation: enum ColorProcessingAlgorithm 
        image_converted = i.Convert(PySpin.PixelFormat_BGR8, PySpin.DIRECTIONAL_FILTER)
        image_data = image_converted.GetData()
        frame = np.frombuffer(image_data, dtype=np.uint8)            
        frame = frame.reshape((i.GetHeight(),i.GetWidth(),3)) 

        corners, ids = find_charuco_board(frame, board, dictionary)
        cv2.aruco.drawDetectedCornersCharuco(frame, corners, ids)
        valid, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(corners, ids, board, intrinsics, dist_coeffs)
        if valid == True:
            cv2.aruco.drawAxis(frame, intrinsics, dist_coeffs, rvec, tvec, 0.2) 

            p3d = [tvec[0][0], tvec[1][0], tvec[2][0]]

            # draw the coordinates
            cv2.putText(frame,"{0:.3f}".format(p3d[0]), (100,200), font, 4,(0,0,255), 6, cv2.LINE_AA)
            cv2.putText(frame,"{0:.3f}".format(p3d[1]), (100,400), font, 4,(0,255,0), 6, cv2.LINE_AA)
            cv2.putText(frame,"{0:.3f}".format(p3d[2]), (100,600), font, 4,(255,0,0), 6, cv2.LINE_AA)



        cv2.imshow("cam1",frame)
    i.Release()
    del i

#
#   cleanup
#

cam.EndAcquisition()
reset_trigger_mode_software(cam)
cam.DeInit()
del cam
del cam_list

system.ReleaseInstance()
del system