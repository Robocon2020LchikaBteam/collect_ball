# coding: UTF-8

from multiprocessing import Process, Value
from ctypes import Structure, c_int
import os
from imageProcessing import ImageProcessing
from debug import ERROR, WARN, INFO, DEBUG, TRACE


"""

test program for image processing

"""


# 共有メモリの構造体
class Point(Structure):
    _fields_ = [('ballAngle', c_int), ('ballDis', c_int)]

def info(title):
    INFO(title)
    INFO('module name:', __name__)
    INFO('parent process:', os.getppid())
    INFO('process id:', os.getpid())

if __name__ == '__main__':
    info('main line')
    # 共有メモリの準備
    shmem = Value(Point, 0)
    # 画像処理インスタンスの生成
    imageProcessing = ImageProcessing()

    p_imageProcessing = Process(target=imageProcessing.target, args=(shmem,))

    p_imageProcessing.start()
    DEBUG('p_imageProcessing started')

    p_imageProcessing.join()
