import cv2
from helper_functions import *


windowName = "Binocular vision"
taskbarName = "Display mode"

displayOptions = ["Side by side", "Red-Green"]

distanceTaskbar = "Distance"

cv2.namedWindow(windowName)
cv2.createTrackbar(taskbarName, windowName, 0, len(displayOptions)-1, callback )	

# disableAutoFocus()

cams = (cv2.VideoCapture(0), cv2.VideoCapture(1))

setCameraResolutions16x9(cams, 720)

while(True):
	image = None
	
	# Capture frame-by-frame
	frames = getFrames(cams)
	
	choice = cv2.getTrackbarPos(taskbarName, windowName)
	
	# Display the resulting frame
	if(choice==0):
		image = sideBySide(frames)
	elif(choice==1):
		cv2.createTrackbar(distanceTaskbar, windowName, getDistance(windowName, distanceTaskbar), getWidth(), callback)
		image = redGreen(getDistance(windowName, distanceTaskbar), frames)
	
	cv2.imshow(windowName, image)
	
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

# When everything done, release the capture
cams[0].release()
cams[1].release()
cv2.destroyAllWindows()
