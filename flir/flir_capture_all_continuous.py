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
ap.add_argument("folder", help="folder to save images")
ap.add_argument("-m", "--master", type=str, default="18284509", help="master camera by id")
ap.add_argument("-f", "--force", action="store_true", help="force overwrite in folder")
ap.add_argument("--fps", type=int, default=20, help="set framerate")

args = vars(ap.parse_args())

# make folder
target_folder = args['folder']
if os.path.isdir(target_folder):
    if args['force'] == False:
        print("{}: error: folder {} exists. Use --force to overwrite files.".format(os.path.basename(sys.argv[0]), target_folder))
        sys.exit()
else:
    os.makedirs(target_folder)



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
master_id = args["master"]
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

worker = ImageWorker()
worker.start()

fps = args["fps"]
fps_report_frequency = fps*2

start = last = time.time()     
last_fps = 0

while 1:
    if cv2.waitKey(1) != -1:
        break

    # wait until 
    while time.time() < (start + 1.0/fps):
        time.sleep(0.01) 

    start = time.time()
    last_fps += 1.0 / (start-last)
    last = time.time()    

    if count % fps_report_frequency == 0:
        print(worker.images.qsize() )
        print("fps {0:.3f}".format( last_fps / fps_report_frequency))        
        last_fps = 0

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
            i.Release()
            del i
        except PySpin.SpinnakerException as ex:
            print("Error: {}".format(ex))

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

