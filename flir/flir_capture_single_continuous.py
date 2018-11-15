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
ap.add_argument("-c", "--camera", type=str, default="0", help="use camera by id")
ap.add_argument("-f", "--force", action="store_true", help="force overwrite in folder")
ap.add_argument("--fps", type=int, default=20, help="set framerate in Hertz")

args = vars(ap.parse_args())

fps = args["fps"]



# make folder
target_folder = args['folder']
if os.path.isdir(target_folder):
    if args['force'] == False:
        print("{}: error: folder {} exists. Use --force to overwrite files.".format(os.path.basename(sys.argv[0]), target_folder))
        sys.exit()
else:
    os.makedirs(target_folder)

def set_fps(cam, fps):
    print("current acquisitionFrameRate", cam.AcquisitionFrameRate.GetValue() )
    cam.AcquisitionFrameRateEnable.SetValue(True)
    print("acquisitionFrameRate Enable", cam.AcquisitionFrameRateEnable.GetValue() )
    cam.AcquisitionFrameRate.SetValue(fps)
    print("acquisitionFrameRate set to", cam.AcquisitionFrameRate.GetValue() )


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
    print("no camera specified (use -c). Using the first one in the list {}".format(camera_serial))


cam = cam_list.GetBySerial(camera_serial)

try:
    cam.Init()
    cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)

    # we now disable the trigger mode and let the camera capture at fps 
    # set_trigger_mode_software(cam)
    reset_trigger_mode_software(cam)
    set_fps(cam, fps)

    cam.BeginAcquisition()

except:
    print("error initializing camera {}".format(camera_serial))
    sys.exit()



print("saving images to folder {}".format(target_folder))
print("stop recording using ctr-c")



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


worker = ImageWorker()
worker.start()

count = 0
fps_report_frequency = fps*2
start_time = time.time()     

try:
  while 1:
    if cv2.waitKey(1) != -1:
        break

    if count % fps_report_frequency == 0:        
        fps = fps_report_frequency / (time.time() - start_time) # / fps_report_frequency
        print("fps {:.3f} image count {}, in buffer {}".format(fps, count,worker.images.qsize() ))        
        start_time = time.time()
    
    #cam.TriggerSoftware()
    i = cam.GetNextImage()
    #print("new one", count)
    #print(i.GetWidth(), i.GetHeight(), i.GetBitsPerPixel())
    cvi = None 

    if i.IsIncomplete():
        pass
    else:
        filename = "{}/cam_{:06}.jpg".format(target_folder,count)
        worker.addImage( (filename, i) )            
        count += 1
    i.Release()
    del i

except KeyboardInterrupt:
    pass
#
#   cleanup
#

worker.stop()

while(1):
    print("{} images to be processed. waiting for thread to finish".format(worker.images.qsize()))
    time.sleep(0.5)
    if worker.images.empty():
        break


cam.EndAcquisition()
reset_trigger_mode_software(cam)
cam.DeInit()
del cam
del cam_list

system.ReleaseInstance()
del system

