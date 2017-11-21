
from queue import Queue
from threading import Thread
from mark import Box
import cv2

class  HOGPeopleDetector(Thread):
    FREQUENCY = 10
    def __init__(self, out_queue):
        Thread.__init__(self, daemon = True)
        self.in_queue = Queue()
        self.out_queue = out_queue
        self.rate = self.FREQUENCY
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def enqueue(self, frame):
        self.rate -= 1
        if self.rate <= 0:
            self.in_queue.put(frame)
            self.rate = self.FREQUENCY

    def run(self):
        while True:
            frame = self.in_queue.get()
            rects, weights = self.hog.detectMultiScale(frame, winStride=(4, 4), padding=(8, 8), scale=1.0555)
            for rect in rects:
                box = Box(rect.x, rect.y, rect.w, rect.h)
                self.out_queue.put(box)
            self.in_queue.task_done()


class  BGPeopleDetector(Thread):
    FREQUENCY = 10
    def __init__(self, out_queue):
        Thread.__init__(self, daemon = True)
        self.in_queue = Queue()
        self.out_queue = out_queue
        self.rate = self.FREQUENCY
        self.first_frame = None

    def enqueue(self, frame):
        self.rate -= 1
        if self.first_frame is None:
            self.first_frame = self.grayframe(frame)
            return
        if self.rate <= 0:
            self.in_queue.put(frame)
            self.rate = self.FREQUENCY

    def grayframe(self, frame):
        #frame = frame[80:, 0:]
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def run(self):
        while True:
            frame = self.in_queue.get()
            frame = self.grayframe(frame)
            frameDelta = cv2.absdiff(self.first_frame, frame)
            _, thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)
            (_, contours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 600: continue
                x, y, w, h = cv2.boundingRect(cnt)
                box = Box(x, y, w, h)
                self.out_queue.put(box)
            self.in_queue.task_done()


class MovementDetector(Thread):
    def __init__(self, out_queue):
        Thread.__init__(self, daemon = True)
        self.in_queue = Queue()
        self.out_queue = out_queue
        self.fgbg = cv2.bgsegm.createBackgroundSubtractorMOG()
        self.kernelOp = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
        self.kernelCl = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,20))

    def enqueue(self, frame):
        self.in_queue.put(frame)

    def run(self):
        while True:
            frame = self.in_queue.get()
            fgmask = self.fgbg.apply(frame)
            ret, mask= cv2.threshold(fgmask,200,255,cv2.THRESH_BINARY)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernelOp)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernelCl)

            image, contours, hierarchy = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
            boxes =[]
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 600: continue
                x, y, w, h = cv2.boundingRect(cnt)
                box = Box(x, y, w, h)
                self.out_queue.put(box)
            self.in_queue.task_done()
