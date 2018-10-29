import sys
import time


fps_report_frequency = 10
fps = 30

count = 0

start = last = time.time() 

last_fps = 0

while(1):
    count += 1

    while time.time() < (start + 1.0/fps):
        time.sleep(0.0001) 

    start = time.time()   
 
    last_fps += 1.0 / (start-last)
    last = time.time()
    
    if count % fps_report_frequency == 0:
        print("fps {0:.3f}".format( last_fps / fps_report_frequency))
        last_fps = 0
