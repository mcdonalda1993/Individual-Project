import numpy as np
import cv2
from helper_functions import *

cam1 = cv2.VideoCapture(0)
checkCamera(cam1)
cam2 = cv2.VideoCapture(1)
checkCamera(cam2)

disableAutoFocus()

run(cam1, cam2)

# When everything done, release the capture
cam1.release()
cam2.release()
cv2.destroyAllWindows()