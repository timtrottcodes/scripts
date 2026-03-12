import numpy as np
import cv2

width = 960
height = 720

# create white image
mask = np.ones((height, width, 3), dtype=np.uint8) * 255

# mask bottom 20%
mask[int(height*0.72):,:,:] = 0

cv2.imwrite("mask.png", mask)
