import numpy as np
import cv2
import sys

def checkCamera(cam):
	if(cam.isOpened()==False):
		sys.exit("A camera is not detected")


cap = cv2.VideoCapture(0)
checkCamera(cap)
cap2 = cv2.VideoCapture(1)
checkCamera(cap2)

while(True):
    
    # Capture frame-by-frame
    ret, frame = cap.read()
    ret2, frame2 = cap2.read()

    # Display the resulting frame
    cv2.imshow('frame', frame)
    cv2.imshow('frame2', frame2)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cap2.release()
cv2.destroyAllWindows()