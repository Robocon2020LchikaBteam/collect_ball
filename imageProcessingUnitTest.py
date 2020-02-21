# coding: UTF-8

from multiprocessing import Value
from ctypes import Structure, c_int
import unittest
from imageProcessing import ImageProcessing
from debug import ERROR, WARN, INFO, DEBUG, TRACE
import cv2
import time
import glob


"""

unit test for imageProcessing.py

"""


class TestPoint(Structure):
    _fields_ = [('ballAngle', c_int), ('ballDis', c_int)]


if __name__ == '__main__':
    TRACE('test main line')
    # テスト用共有メモリの準備
    shmem = Value(TestPoint, 0)

    imageProcessing = ImageProcessing()

    file_path = 'data/temp/camera_capture_wall_6.jpg'

    TRACE(file_path)
    stream = cv2.imread(file_path)

    ball_angle, ball_distance, station_angle, station_distance, wall_x, wall_size = imageProcessing.imageProcessingFrame(stream, shmem)
   
    cv2.imshow('Frame', cv2.flip(stream, -1))
    cv2.moveWindow('Frame', 0, 30)
    cv2.moveWindow('MaskRED', 482, 30)
    cv2.moveWindow('MaskYELLOW', 964, 30)
    cv2.moveWindow('MaskGREEN', 1446, 30)
    cv2.moveWindow('MaskBLACK', 0, 530)
    cv2.waitKey(0)

    cv2.destroyAllWindows()
