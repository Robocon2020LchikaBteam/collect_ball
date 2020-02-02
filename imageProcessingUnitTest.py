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

    file_path = 'pic/picture_0_10.jpg'

    TRACE(file_path)
    stream = cv2.imread(file_path)

    red_ball_angle, red_ball_distance = imageProcessing.imageProcessingFrame(stream, shmem)
   
    TRACE(red_ball_angle, red_ball_distance)
    cv2.imshow('Frame', stream)
    cv2.moveWindow('Frame', 0, 30)
    cv2.moveWindow('MaskRed', 482, 30)
    cv2.waitKey(0)

    cv2.destroyAllWindows()
