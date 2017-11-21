import cv2


class Bookmark:
    def __init__(self, mark):
        self._mark = mark


class Buffer:
    def __init__(self, size):
        self._buffer = []
        self._max_size = size
    
    def push(self, val):
        if len(self._buffer) >= self._max_size:
            self._buffer = self._buffer[1:]
        self._buffer.append(val)


class Capture:
    def __init__(self, name):
        self._name = name
        self._capture = None

    @property
    def width(self):
        return int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)) 

    @property
    def height(self):
        return int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) 

    def start(self):
        self._capture = cv2.VideoCapture(self._name)

    def stop(self):
        self._capture.release()

    def seek_position(self, pos):
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, pos)
    
    def seek(self, pos):
        self.seek_position(self.length * pos)

    @property
    def length(self):
        return int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT))

    @property
    def position(self):
        return int(self._capture.get(cv2.CAP_PROP_POS_FRAMES))

    def is_ready(self):
        return self._capture.isOpened()

    def read(self):
        return self._capture.read()

    def release(self):
        self.stop()
        
    def __del__(self):
        self.release()


class Box:
    def __init__(self, x,y,w=0,h=0):
        self._x = x
        self._y = y
        self._w = w
        self._h = h

    @property
    def left(self):
        return self._x
        
    @property
    def right(self):
        return self._x + self._w

    @right.setter
    def set_right(self, r):
        self._w = r - self._x

    @property
    def top(self):
        return self._y

    @property
    def bottom(self):
        return self._y + self._h

    @bottom.setter
    def set_bottom(self, b):
        self._h = b - self._y

    @property
    def area(self):
        return self._w * self._h

    @property
    def center(self):
        x = (self.left + self.right)/2
        y = (self.top + self.bottom)/2
        return x, y
    
    def points(self):
        return (self.left, self.top), (self.right, self.bottom)

    def vertical_overlap(self, box):
        return max(0, min(self.bottom, box.bottom) - max(self.top, box.top))

    def vertically_overlaps(self, box):
        return self.vertical_overlap(box) > 0

    def horizontal_overlap(self, box):
        return max(0, min(self.right, box.right) - max(self.left, box.left))

    def horizontally_overlaps(self, box):
        return self.horizontal_overlap(box) > 0

    @staticmethod
    def merge(rectangles):
        if len(rectangles)==0:
            return Box(0,0,0,0)
        MAX = 1000 * 1000 
        minx, miny = MAX, MAX
        maxx, maxy = -MAX, -MAX
        for r in rectangles:
            minx = min(r.left, minx)
            miny = min(r.top, miny)
            maxx = max(r.right, maxx)
            maxy = max(r.bottom, maxy)
        return Box(minx, miny, maxx - minx, maxy - miny)

    def vertical_overlap_ratio(self, box):
        rv = 0
        delta = min(self.bottom - self.top, box.bottom - box.top)
        if box.top <= self.top and self.top <= box.bottom and box.bottom <= self.bottom:
            rv = (box.bottom - self.top) / delta
        elif self.top <= self.top and self.top <= self.bottom and self.bottom <= box.bottom:
            rv = (self.bottom - self.top) / delta
        elif self.top <= self.top and self.top <= box.bottom and box.bottom <= self.bottom:
            rv = (box.bottom - self.top) / delta
        elif self.top <= self.top and self.top <= self.bottom and self.bottom <= box.bottom:
            rv = (self.bottom - self.top) / delta
        return rv

    def overlap_ratio(self, box):
        intersectionWidth = max(0, min(self.right, box.right) - max(self.left, box.left))
        intersectionHeight = max(0,	min(self.bottom, box.bottom) - max(self.top, box.top))
        intersectionArea = max(0, intersectionWidth * intersectionHeight)
        unionArea = self.area + box.area - intersectionArea
        return intersectionArea / unionArea

    def shrink(self, wfactor, hfactor):
        wpad, hpad = int(wfactor*self._w), int(hfactor*self._h)
        self._x += wpad
        self._y += hpad
        self._w -= wpad
        self._h -= hpad

    def inflate(self, val):
        self._x -= val
        self._y -= val
        self._w += val
        self._h += val
        
    def expand(self, wfactor, hfactor):
        wpad, hpad = int(wfactor*self._w), int(hfactor*self._h)
        self._x -= wpad
        self._y -= hpad
        self._w += wpad
        self._h += hpad
    
    def intercept(self, box):
        self._x = max(self.left, box.left)
        self._y = max(self.top, box.top)
        self._w = min(self.right, box.right) - self.left
        self._h = min(self.bottom, box.bottom) - self.top

    def set_position(self, left, top):
        self._x = left
        self._y = top
    
    def move(self, left, top):
        self.set_position(self.left + left, self.top + top)

    def __str__(self):
        return "x = {x}; y = {y}; w = {w}; h = {h}".format(x=self._x, y=self._y, w=self._w, h=self._h)

class MainLoop:
    PAUSED  = 0
    PLAYING = 1
    STOPPED = 2

    def __init__(self, service, status=PAUSED):
        self._status = status
        self._service= service

    def play(self):
        self._service.start()
        self._status = MainLoop.PLAYING
        while self._service.is_ready():
            self._service

    def stop(self):
        self._service.stop()
        self._status = MainLoop.STOPPED


class EventDispatcher:
    def __init__(self):
        self._listeners = {}

    def dispatch(self, eventName, data=None):
        for listener in self._listeners.get(eventName, []):
            listener(self, data)

    def addListener(self, eventName, listener):
        if eventName not in self._listeners:
            self._listeners[eventName] = []
        self._listeners[eventName].append(listener)


class Person:
    def __init__(self):
        self._box = Box(0,0)

    