import cv2
from helper_functions import *


windowName = "Binocular vision"
taskbarName = "Display mode"
cv2.namedWindow(windowName)
cv2.createTrackbar(taskbarName, windowName, 0, noOfDisplayOptions()-1, callback )	

# disableAutoFocus()

cam0 = cv2.VideoCapture(0)
cam1 = cv2.VideoCapture(1)

setCameraResolutions16x9(cam0, cam1, 720)

while(True):
	
	frame = None
	frame2 = None
	
	## Will allow for plug an play of camera, however slows capture
	# cam0 = getCamera(cam0, 0)
	# cam1 = getCamera(cam1, 1)
	
	# Capture frame-by-frame
	frame = getFrame(cam0)
	frame2 = getFrame(cam1)
	
	# Display the resulting frame
	display(windowName, cv2.getTrackbarPos(taskbarName, windowName), frame, frame2)
	
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

# When everything done, release the capture
cam0.release()
cam1.release()
cv2.destroyAllWindows()
