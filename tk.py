import sys
from PIL import Image, ImageTk
import tkinter as tk
from tkinter.constants import *
import argparse
import cv2
import os
from mark import *
from queue import Queue, Empty
from peoplefinder import BGPeopleDetector, MovementDetector

class Application:
    def __init__(self, capture):
        self.capture = capture 
        self.capture.start()
        self.dispatcher = EventDispatcher()
        self.queue = Queue()
        self.people_detector = BGPeopleDetector(self.queue)
        self.movement_detector = MovementDetector(self.queue)
        self.people_detector.start()
        self.movement_detector.start()

        self.root = tk.Tk()
        self.people = []
        
        self.root.title("Nerds counter")
        self.root.protocol('WM_DELETE_WINDOW', self.destructor)
        self.root.config(cursor="arrow")
        
        self.box = Box(0,0)
        # image main_image
        self.main_image = tk.Label(self.root)
        self.main_image.grid(row=0, column=0, rowspan=2)
        self.main_image.bind("<Button-1>", self.on_mouse_click)
        self.main_image.bind("<B1-Motion>", self.on_mouse_move)
        # image binary_image
        self.binary_image = tk.Label(self.root)
        self.binary_image.grid(row=0, column=1, sticky=N)

        # create slider
        position = tk.Scale(self.root, from_=0, to=1000, orient=tk.HORIZONTAL, resolution=4, command=self.seek_video)
        position.grid(row=2, column=0, columnspan=2)
        #self.dispatcher.addListener('new-frame', lambda s, e: position.set(self.capture.position))
        self.video_loop()
         
    def video_loop(self):
        ok, frame = self.capture.read()
        frame = cv2.resize(frame, (800, 600), frame)

        if ok:
            self.people_detector.enqueue(frame)
            #self.movement_detector.enqueue(frame)

            k = cv2.waitKey(1) & 0xff
            self.dispatcher.dispatch('new-frame')

            try:
                while True:
                    box = self.queue.get_nowait()
                    p1, p2 = box.points()
                    frame = cv2.rectangle(frame, p1, p2, (34, 250, 10), 2)
            except Empty:
                pass

            p1, p2 = self.box.points()
            frame = cv2.rectangle(frame,p1,p2,(200,255,100),3)
            main_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            main_image = Image.fromarray(main_image)
            main_imgtk = ImageTk.PhotoImage(image=main_image)  
            self.main_image.imgtk = main_imgtk
            self.main_image.config(image=main_imgtk)

            frame = cv2.resize(frame, (400, 300), frame)
            binary_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            binary_image = Image.fromarray(binary_image)
            binary_imgtk = ImageTk.PhotoImage(image=binary_image)
            self.binary_image.imgtk = binary_imgtk
            self.binary_image.config(image=binary_imgtk)
        self.root.after(10, self.video_loop)
 
    def seek_video(self, val):
        self.capture.seek(float(val)/1000.0)


    def on_mouse_click(self, event):
        self.box = Box(event.x, event.y)

        
    def on_mouse_move(self, event):
        self.box.set_right = event.x
        self.box.set_bottom = event.y

    def destructor(self):
        self.root.destroy()
        self.capture.release()


def main():
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default="./", help="path to output directory to store snapshots (default: current folder")
    ap.add_argument("-i", "--input", help="path to input file to reproduce")
    args = vars(ap.parse_args())
    
    # start the app
    print(args)
    capture = Capture(args["input"])
    pba = Application(capture)
    pba.root.mainloop()


if __name__=='__main__':
    sys.exit(main())

