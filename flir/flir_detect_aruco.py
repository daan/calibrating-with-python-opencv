import sys
import time
import PySpin

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


def set_trigger_mode(cam, triggerSource):
    cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
    cam.TriggerSource.SetValue(triggerSource)
    cam.TriggerMode.SetValue(PySpin.TriggerMode_On)

def reset_trigger_mode_software(cam):
    cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
    print("reset trigger mode")

#
#   setup
#

system = PySpin.System.GetInstance()
cam_list = system.GetCameras()

master_id = "18284509"
master = None

print("number of cameras {}".format(cam_list.GetSize()))


if cam_list.GetSize() == 0:
    print("no cameras found, aborting")
    system.ReleaseInstance()
    del system
    sys.exit()

cameras = []
for i in range(cam_list.GetSize()):
    try:
        cam = cam_list.GetByIndex(i)
        cam_id = cam.GetUniqueID()
        cam.Init()
    

        if cam_id == master_id:
            print("master: {}".format(cam_id))
            master = cam
            set_trigger_mode(cam, PySpin.TriggerSource_Software)
        else:
            print("follower: {}".format(cam_id))
            set_trigger_mode(cam, PySpin.TriggerSource_Line3)
        cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        cam.BeginAcquisition()
        cameras.append(cam)
    except PySpin.SpinnakerException as ex:
        print("Error: {}".format(ex))


#
#   loop
#


count = 0
size = 4
frame = {}

camera_dict = { "18284509": "", "18284511": "_1", "18284512": "_2"}


dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)

print("start loop")

while 1:

    key = cv2.waitKey(1)

    if key == 27: # ESC
        cv2.destroyAllWindows()
        break

    try:
        master.TriggerSoftware.Execute()
    except PySpin.SpinnakerException as ex:
        print("Error: {}".format(ex))

    for cam in cameras:
        try:
            i = cam.GetNextImage()
            #print(i.GetWidth(), i.GetHeight(), i.GetBitsPerPixel())

            if i.IsIncomplete():
                pass
            else:            
                cam_id = cam.GetUniqueID()
                # see documentation: enum ColorProcessingAlgorithm 
                image_converted = i.Convert(PySpin.PixelFormat_BGR8, PySpin.DIRECTIONAL_FILTER)
                image_data = image_converted.GetData()
                cvi = np.frombuffer(image_data, dtype=np.uint8)
                cvi = cvi.reshape((i.GetHeight(),i.GetWidth(),3)) 

                corners, ids = detect_aruco_markers(frame, dictionary)

                frame[cam_id] = cvi

                res = cv2.resize(cvi, (int(1280/size),int(1024/size)))
                cv2.imshow("cam{}".format(cam_id),res)
            i.Release()
            del i
        except PySpin.SpinnakerException as ex:
            print("Error: {}".format(ex))

#
#   cleanup
#

del master
for cam in cameras:
    cam.EndAcquisition()
    reset_trigger_mode_software(cam)
    cam.DeInit()
    del cam
del cameras
del cam_list

system.ReleaseInstance()
del system