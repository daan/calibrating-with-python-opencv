import sys
import time
import PySpin
import os

import numpy as np
import cv2

from queue import Queue
import threading

import argparse

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--camera", type=str, default="0", help="camera by id")

args = vars(ap.parse_args())

def set_trigger_mode(cam, triggerSource):
    cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
    cam.TriggerSource.SetValue(triggerSource)
    cam.TriggerMode.SetValue(PySpin.TriggerMode_On)

def reset_trigger_mode_software(cam):
    cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
    print("reset trigger mode")


def reset_trigger_mode_software(cam):
    cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
    print("reset trigger mode")


#
#   setup
#

master_id = "18284509"
master = None


system = PySpin.System.GetInstance()
cam_list = system.GetCameras()

if cam_list.GetSize() == 0:
    print("no cameras found, aborting")
    system.ReleaseInstance()
    del system
    sys.exit()

for i in range(cam_list.GetSize()):
    cam = cam_list.GetByIndex(i)
    print("camera {} serial: {}".format(i, cam.GetUniqueID()))



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
        sys.exit()


class ImageWorker(threading.Thread):
    def __init__(self):
        super(ImageWorker, self).__init__()
        self.images = Queue()
        self._stop_event = threading.Event()

    def addImage(self, img):
        self.images.put(img)
    def stop(self):
        self._stop_event.set()
    def stopped(self):
        return self._stop_event.is_set()
    def run(self):
        print("run")
        while(1):        
            if self.images.empty():
                if self.stopped():
                    break
                else:
                    time.sleep(0.10)
            else:
                item = self.images.get()
                
                if item != None:
                    filename, i = item
                    
                    #i.save(filename)

                    image_converted = i.Convert(PySpin.PixelFormat_BGR8, PySpin.DIRECTIONAL_FILTER)
                    
                    #writing with spinaker

                    image_converted.Save(filename)

                    #writing with opencv

                    #image_data = image_converted.GetData()
                    #cvi = np.frombuffer(image_data, dtype=np.uint8)            
                    #cvi = cvi.reshape((i.GetHeight(),i.GetWidth(),3)) 
                    #cv2.imwrite(filename, cvi)




#
#   loop
#

count = 0
elapsed = 0

#os.makedirs("captures", exist_ok=True)

worker = ImageWorker()
worker.start()


blank_image = np.zeros((300,400,3), np.uint8)
cv2.imshow("blank", blank_image)

print("start capturing")

while 1:
    key = cv2.waitKey(1)

    start = time.time()

    

    if key == 27: # ESC
        cv2.destroyAllWindows()
        break
    

    try:
        master.TriggerSoftware.Execute()
        count += 1
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
                filename = "captures/cam_{}__{}.jpg".format(cam_id, count)
                worker.addImage( (filename, i) )            
                # see documentation: enum ColorProcessingAlgorithm 
                #image_converted = i.Convert(PySpin.PixelFormat_BGR8, PySpin.DIRECTIONAL_FILTER)
                #image_data = image_converted.GetData()
                #cvi = np.frombuffer(image_data, dtype=np.uint8)
                #cvi = cvi.reshape((i.GetHeight(),i.GetWidth(),3)) 
                #frame[cam_id] = cvi

                #res = cv2.resize(cvi, (int(1280/size),int(1024/size)))
                #cv2.imshow("cam{}".format(cam_id),res)
            i.Release()
            del i
        except PySpin.SpinnakerException as ex:
            print("Error: {}".format(ex))

    

    end = time.time()
    elapsed += end - start
    
    if count % 10 == 0:
        print(worker.images.qsize() )
        print("fps {0:.3f}".format(10 /elapsed))
        
        elapsed = 0

#
#   cleanup
#

worker.stop()

while(1):
    print("{} images to be processed. waiting for thread to finish".format(worker.images.qsize()))
    time.sleep(0.5)
    if worker.images.empty():
        break

for cam in cameras:
    cam.EndAcquisition()
    reset_trigger_mode_software(cam)
    cam.DeInit()
    del cam
del cameras
del cam_list

system.ReleaseInstance()
del system

