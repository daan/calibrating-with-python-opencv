import sys
import time
import PySpin

import numpy as np
import cv2



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

print("number of cameras {}".format(cam_list.GetSize()))

if cam_list.GetSize() == 0:
    print("no cameras found, aborting")
    system.ReleaseInstance()
    del system
    sys.exit()

cameras = []
for i in range(cam_list.GetSize()):
    cam = cam_list.GetByIndex(i)
    print("camera {} serial: {}".format(i, cam.GetUniqueID()))
    cam.Init()
    cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
    set_trigger_mode_software(cam)
    cam.BeginAcquisition()
    cameras.append(cam)


#
#   loop
#

count = 0

while 1:

    if cv2.waitKey(1) == 27: # ESC
        cv2.destroyAllWindows()
        break

    for cam in cameras:
        cam.TriggerSoftware()
        i = cam.GetNextImage()
        #print(i.GetWidth(), i.GetHeight(), i.GetBitsPerPixel())

        if i.IsIncomplete():
            pass
        else:            
            # see documentation: enum ColorProcessingAlgorithm 
            image_converted = i.Convert(PySpin.PixelFormat_BGR8, PySpin.DIRECTIONAL_FILTER)
            image_data = image_converted.GetData()
            cvi = np.frombuffer(image_data, dtype=np.uint8)            
            cvi = cvi.reshape((i.GetHeight(),i.GetWidth(),3)) 
            print(cvi.shape)       
            cv2.imshow("cam1",cvi)
        i.Release()
        del i

#
#   cleanup
#

for cam in cameras:
    cam.EndAcquisition()
    reset_trigger_mode_software(cam)
    cam.DeInit()
    del cam
del cameras
del cam_list

system.ReleaseInstance()
del system