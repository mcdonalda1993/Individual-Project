
import os
import numpy as np
import cv2

display_options = ["Side by side", "Red-Green"]
width = 0 
height = 0

def noOfDisplayOptions():
	return len(display_options)

def getCamera(cam, number):
	if (cam == None) or (cam.isOpened() == False):
		return cv2.VideoCapture(number)
		
def getFrame(cam):
	global height, width
	try:
		ret, frame = cam.read()
		(height, width, depth) = frame.shape
		return frame
	except:
		return None
		
def disableAutoFocus():
	## If that doesn't work try, sudo apt-get install v4l-utils
	os.system('v4l2-ctl -d 0 -c focus_auto=0')
	os.system('v4l2-ctl -d 0 -c focus_absolute=20')
	os.system('v4l2-ctl -d 1 -c focus_auto=0')
	os.system('v4l2-ctl -d 1 -c focus_absolute=20')

def setFocus(cam, focus):
	os.system('v4l2-ctl -d '+ str(cam) +' -c focus_absolute=' + str(focus))
	
def callback(value):
	pass

def display(window, choice, frame, frame2):
	if(choice==0):
		sideBySide(window, frame, frame2)
	elif(choice==1):
		pass

def returnValidImage(image):
	if image != None:
		return image
	else:
		blank_image = np.zeros((height,width,3), np.uint8)
		return blank_image

def sideBySide(window, frame, frame2):
	image = None
	imagePart1 = returnValidImage(frame)
	imagePart2 = returnValidImage(frame2)
	image = np.hstack((imagePart1, imagePart2))
	cv2.imshow(window, image)