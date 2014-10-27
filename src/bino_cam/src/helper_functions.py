import sys
import os
import Tkinter

def checkCamera(cam):
	if(cam.isOpened()==False):
		sys.exit("A camera is not detected")
		
def disableAutoFocus():
	# Try first, need to sudo apt-get install uvcdynctrl
	os.system('uvcdynctrl --device=/dev/video0 --set=\'Focus, Auto\' 0')
	os.system('uvcdynctrl --device=/dev/video0 --set=\'Focus (absolute)\' 20')
	os.system('uvcdynctrl --device=/dev/video1 --set=\'Focus, Auto\' 0')
	os.system('uvcdynctrl --device=/dev/video1 --set=\'Focus (absolute)\' 20')
	
	## If that doesn't work try, sudo apt-get install v4l-utils
	os.system('v4l2-ctl -d 0 -c focus_auto=0')
	os.system('v4l2-ctl -d 0 -c focus_absolute=20')
	os.system('v4l2-ctl -d 1 -c focus_auto=0')
	os.system('v4l2-ctl -d 1 -c focus_absolute=20')

def setFocus(cam, focus):
	# Try
	os.system('uvcdynctrl --device=/dev/video' + str(cam) +  ' --set=\'Focus (absolute)\' ' + str(focus))
	# or
	os.system('v4l2-ctl -d '+ str(cam) +' -c focus_absolute=' + str(focus))

def run(cam1, cam2):
	
top = Tkinter.Tk()
# Code to add widgets will go here...
frame = Frame(top)
frame.pack()

redbutton = Button(frame, text="Red", fg="red")
redbutton.pack( side = LEFT)

top.mainloop()
	
	while(True):
	    
	    # Capture frame-by-frame
	    ret, frame = cam1.read()
	    ret2, frame2 = cam2.read()

	    # Display the resulting frame
	    cv2.imshow('frame', frame)
	    cv2.imshow('frame2', frame2)
	    
	    if cv2.waitKey(1) & 0xFF == ord('q'):
	        break