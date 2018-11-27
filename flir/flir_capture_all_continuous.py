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

ap.add_argument("--openpose",  action="store_true", help="name images for openpose (e.g. 000000000000_rendered, ..._1, ..._2, ...)")

args = vars(ap.parse_args())

save_for_openpose = args['openpose']

fps = args["fps"]

# make folder
target_folder = args['folder']
if os.path.isdir(target_folder):
    if not args['force']:
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
            #set_trigger_mode(cam, PySpin.TriggerSource_Software)
            set_fps(cam, fps)
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


images = [None, None, None]

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

        

        for n in range(len(cameras)):
            cam = cameras[n]
            try:
                # milliseconds.
                try:
                    if n == 0:
                        i = cam.GetNextImage()
                    else:
                        i = cam.GetNextImage(20)
                #print(i.GetWidth(), i.GetHeight(), i.GetBitsPerPixel())
                except PySpin.SpinnakerException as ex:
                    print("none")
                    continue

                if i.IsIncomplete():
                    print("incomplete")
                    pass
                else:
                    if n == 0:
                        print("new frame")
                        count += 1
                        images = [None, None, None]

                    print(n, time.time() )            

                    cam_id = cam.GetUniqueID()

                    if save_for_openpose:
                        if n == 0:
                            filename = "{}/{:012}_rendered.jpg".format(target_folder, count)
                        else:
                            filename = "{}/{:012}_rendered_{}.jpg".format(target_folder, count, n)
                    else:
                        filename = "{}/cam_{}__{:06}.jpg".format(target_folder, cam_id, count)
                    #print(filename, count[n], cam_id)
                    
                    images[n] = (filename, i)
                    #worker.addImage( (filename, i) )


                i.Release()
                del i
            except PySpin.SpinnakerException as ex:
                print("Error: {}".format(ex))
        # after a capture round of all cameras. 
        if (images[0] is not None) and (images[1] is not None) and (images[2] is not None):
            print("got three images")
            worker.addImage( images[0])
            worker.addImage( images[1])
            worker.addImage( images[2])


    
except KeyboardInterrupt:
    pass
#
#   cleanup
#

worker.stop()

while(1):
 
    print("{} images to be processed. waiting for thread to finish".format(worker.images.qsize()))
    time.sleep(0.5)

    done = True
    if worker.images.empty():
        break


master = None

for cam in cameras:
    cam.EndAcquisition()
    reset_trigger_mode_software(cam)
    cam.DeInit()
    del cam

del cameras
del cam_list

system.ReleaseInstance()
del system
