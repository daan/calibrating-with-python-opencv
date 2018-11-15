import sys
import time
import PySpin
import os

import numpy as np
import cv2


import argparse

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


os.mkdir(camera_serial)



#
#   loop
#

count = 0

while 1:
    key = cv2.waitKey(1)



    if key == 27: # ESC
        cv2.destroyAllWindows()
        break
    
    #cam.TriggerSoftware()
    i = cam.GetNextImage()
    print(count)
    #print(i.GetWidth(), i.GetHeight(), i.GetBitsPerPixel())
    cvi = None 

    if i.IsIncomplete():
        pass
    else:            
        # see documentation: enum ColorProcessingAlgorithm 
        image_converted = i.Convert(PySpin.PixelFormat_BGR8, PySpin.DIRECTIONAL_FILTER)
        image_data = image_converted.GetData()
        cvi = np.frombuffer(image_data, dtype=np.uint8)            
        cvi = cvi.reshape((i.GetHeight(),i.GetWidth(),3)) 
        cv2.imshow("cam1",cvi)
    i.Release()
    del i

    if key == 32:
        cv2.imwrite("{}/capture_{}.jpg".format(camera_serial,count), cvi)
        count+= 1
        print("saved image {}".format(count))
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