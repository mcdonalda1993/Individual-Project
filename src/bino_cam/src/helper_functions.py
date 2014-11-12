
import os
import numpy as np
import cv2

displayOptions = ["Side by side", "Red-Green"]
taskbarName = "Distance"
width = 0 
height = 0

def noOfDisplayOptions():
	return len(displayOptions)
	
def getCamera(cam, number):
	if (cam == None) or (cam.isOpened() == False):
		return cv2.VideoCapture(number)
		
def getFrame(cam):
	try:
		ret, frame = cam.read()
		return frame
	except:
		return None
		
def getRedGreenTaskbarName():
	return taskbarName

def getDistance(window):
	position = cv2.getTrackbarPos(taskbarName, window)
	if(position == -1):
		return 0
	else:
		return position
		
def getWidth():
	return width
		
def disableAutoFocus():
	## If that doesn't work try, sudo apt-get install v4l-utils
	os.system('v4l2-ctl -d 0 -c focus_auto=0')
	os.system('v4l2-ctl -d 0 -c focus_absolute=20')
	os.system('v4l2-ctl -d 1 -c focus_auto=0')
	os.system('v4l2-ctl -d 1 -c focus_absolute=20')

def setFocus(cam, focus):
	os.system('v4l2-ctl -d '+ str(cam) +' -c focus_absolute=' + str(focus))
	
def setCameraResolutions(cam, cam2, w, h):
	if(cam != None and cam.isOpened()):
		__setCameraResolution(cam, w, h)
	if(cam2 != None and cam2.isOpened()):
		__setCameraResolution(cam2, w, h)

def setCameraResolutions16x9(cam, cam2, h):
	w = 16 * (h/9)
	if(cam != None):
		__setCameraResolution(cam, w, h)
	if(cam2 != None):
		__setCameraResolution(cam2, w, h)

def callback(value):
	pass

def sideBySide(window, frame, frame2):
	image = None
	imagePart1 = __returnValidImage(frame)
	imagePart2 = __returnValidImage(frame2)
	image = np.hstack((imagePart1, imagePart2))
	cv2.imshow(window, image)

def redGreen(window, frame, frame2):
	image = None
	imagePart1 = __getRedImage(frame)
	imagePart2 = __getGreenBlueImage(frame2)
	image = __combineImages(getDistance(window), imagePart1, imagePart2)
	cv2.imshow(window, image)

def __setCameraResolution(cam, w, h):
	global width, height 
	cam.set(3, w)
	cam.set(4, h)
	width = int(cam.get(3))
	height = int(cam.get(4))

def __returnValidImage(image):
	if image != None:
		return image
	else:
		blank_image = np.zeros((height, width, 3), np.uint8)
		return blank_image

def __getRedImage(image=None): 
	red = np.zeros((height, width, 3), np.uint8)
	if image != None:
		red[:,:,2] = image[:,:,2]	#(B, G, R)
	return red
	
def __getGreenBlueImage(image=None): 
	greenBlue = np.zeros((height, width, 3), np.uint8)
	if image != None:
		greenBlue[:,:,:2] = image[:,:,:2]	# (B, G, R)
	return  greenBlue

def __combineImages(distance, image1, image2):
	totalWidth = width + distance
	image = np.zeros((height, totalWidth, 3), np.uint8)
	image[:, :width, 2] = image1[:, :, 2]
	image[:, distance:, :2] = image2[:, :, :2]
	return image
