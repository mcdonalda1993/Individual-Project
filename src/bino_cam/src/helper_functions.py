
import os
import numpy as np
import cv2

displayOptions = ["Side by side", "Red-Green"]
taskbarName = "Distance"
width = 0 
height = 0

def noOfDisplayOptions():
	return len(displayOptions)

def callback(value):
	pass
		
def disableAutoFocus():
	## If that doesn't work try, sudo apt-get install v4l-utils
	os.system('v4l2-ctl -d 0 -c focus_auto=0')
	os.system('v4l2-ctl -d 0 -c focus_absolute=20')
	os.system('v4l2-ctl -d 1 -c focus_auto=0')
	os.system('v4l2-ctl -d 1 -c focus_absolute=20')

def setFocus(cam, focus):
	os.system('v4l2-ctl -d '+ str(cam) +' -c focus_absolute=' + str(focus))

def setCameraResolution(cam, w, h):
	global width, height 
	width = w
	height = h
	cam.set(3, width)
	cam.set(4, height)	

def getCamera(cam, number):
	if (cam == None) or (cam.isOpened() == False):
		return cv2.VideoCapture(number)
		
def getFrame(cam):
	try:
		ret, frame = cam.read()
		return frame
	except:
		return None

def display(window, choice, frame, frame2):
	if(choice==0):
		sideBySide(window, frame, frame2)
	elif(choice==1):
		redGreen(window, frame, frame2)

def sideBySide(window, frame, frame2):
	image = None
	imagePart1 = returnValidImage(frame)
	imagePart2 = returnValidImage(frame2)
	image = np.hstack((imagePart1, imagePart2))
	cv2.imshow(window, image)

def returnValidImage(image):
	if image != None:
		return image
	else:
		blank_image = np.zeros((height, width, 3), np.uint8)
		return blank_image

def redGreen(window, frame, frame2):
	image = None
	imagePart1 = getRedImage(frame)
	imagePart2 = getGreenBlueImage(frame2)
	image = combineImages(getDistance(window), imagePart1, imagePart2)
	cv2.imshow(window, image)
	cv2.createTrackbar(taskbarName, window, getDistance(window), width, callback)	

def getRedImage(image=None):
	red = np.zeros((height, width, 3), np.uint8)
	if image != None:
		red[:,:,2] = image[:,:,2]	#(B, G, R)
	return red
	
def getGreenBlueImage(image=None):
	greenBlue = np.zeros((height, width, 3), np.uint8)
	if image != None:
		greenBlue[:,:,:2] = image[:,:,:2]	# (B, G, R)
	return  greenBlue

def getDistance(window):
	position = cv2.getTrackbarPos(taskbarName, window)
	if(position == -1):
		return 0
	else:
		return position

def combineImages(distance, image1, image2):
	totalWidth = width + distance
	image = np.zeros((height, totalWidth, 3), np.uint8)
	image[:, :width, 2] = image1[:, :, 2]
	image[:, distance:, :2] = image2[:, :, :2]
	return image
