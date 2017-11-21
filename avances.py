#!/usr/bin/python3

import numpy as np
import cv2
import time
from mark import Capture, Box

def close(b1, b2):
    b1x, b1y = b1.center
    b2x, _ = b2.center
    return (b1x -20 < b2x < b1x + 20)

def merge_boxes(boxes):
    return cv2.groupRectangles(boxes, 1, 0) 

def merge_boxes2(boxes):
    merged = True
    t = []
    i = 0
    while merged:
        merged = False
        while i < len(boxes)-1:
            b1, b2 = boxes[i], boxes[i+1] 
            if close(b1, b2):
                t.append(Box.merge([b1, b2]))
                i = i + 1
                merged = True
            else:
                t.append(b1)
            i = i + 1
        boxes = t
    return boxes

'''
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) 
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) 
area = width*height
min_area = 600
max_area = area/2.0

cv2.namedWindow('Camera',cv2.WINDOW_NORMAL)
cv2.namedWindow('Binary',cv2.WINDOW_NORMAL)

cv2.moveWindow("Camera", 1,1);
cv2.moveWindow("Binary", width + 10, 1);
cv2.resizeWindow('Camera', width,height)
cv2.resizeWindow('Binary', width,height)
'''


#fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True) 
fgbg = cv2.bgsegm.createBackgroundSubtractorMOG(history=40) 
kernelOp = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
kernelOp2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(4,4))
kernelCl = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,20))
kernelCl2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,35))

#fourcc = cv2.VideoWriter_fourcc(*'XVID')
#out = cv2.VideoWriter('cortes.avi', fourcc, 20.0, (640,480))
counter = 0

capture = Capture('/home/lontivero/Videos/00010000253000200.mp4')
capture.start()
pos = 0.0
capture.seek(0.0)

while(capture.is_ready()):
    ret, frame = capture.read() #read a frame
    
    #frame = frame[85:, 0:]

    fgmask = fgbg.apply(frame) #Use the substractor

    ret,mask= cv2.threshold(fgmask,100,255,cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernelOp)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernelCl)
    
    contoursimg, contours, hierarchy = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 200: continue # or area > 20000: continue
        
        #if area < min_area or area > max_area: 
        #    continue

        #################
        #   TRACKING    #
        #################            
        M = cv2.moments(cnt)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        x,y,w,h = cv2.boundingRect(cnt)
        boxes.append( (x,y,w,h) )
        #if cx in range(left,right):

        #################
        #   DIBUJOS     #
        #################
        #cv2.circle(frame,(cx,cy), 8, (0,0,255), -1)
        #frame = cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)            
        cv2.drawContours(frame, cnt, -1, (0,255,100), 1)

    boxes, _ = merge_boxes(boxes)
    for (x, y, w, h) in boxes:
        p1, p2 = Box(x, y, w, h).points()
        frame = cv2.rectangle(frame,p1,p2,(200,255,100),3)            

    '''
    counter_str = 'Nerds: '+ str(counter)
    cv2.putText(frame, counter_str ,(10,40),cv2.FONT_HERSHEY_SIMPLEX,1,(255,0,0),2,cv2.LINE_AA)
    '''

    cv2.imshow('Camera',frame)
    cv2.imshow('Binary',mask)
    
    #Abort and exit with 'Q' or ESC
    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break
    if k == ord('s'):
        pos += 0.01
        capture.seek(pos)
    if k == ord('a'):
        pos -= 0.01
        capture.seek(pos)
    if k == ord('S'):
        pos += 0.1
        capture.seek(pos)
    if k == ord('A'):
        pos -= 0.1
        capture.seek(pos)

#out.release()
capture.stop()
cv2.destroyAllWindows() #close all openCV windows