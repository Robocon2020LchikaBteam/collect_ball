# coding: UTF-8

from multiprocessing import Process, Value
from ctypes import Structure, c_int, c_bool
import os
from motorContl import MotorController
from imageProcessing import ImageProcessing
from imu import Imu
# from socketServer import Server
from debug import ERROR, WARN, INFO, DEBUG, TRACE

"""

main module

"""


# 共有メモリの構造体
class Point(Structure):
    _fields_ = [('ballAngle', c_int), ('ballDis', c_int),
                ('stationAngle', c_int), ('stationDis', c_int),
                ('bodyAngle', c_int), ('preparingRestart', c_bool), ('relyStation', c_bool)]


def info(title):
    INFO(title)
    INFO('module name:', __name__)
    INFO('parent process:', os.getppid())
    INFO('process id:', os.getpid())


if __name__ == '__main__':
    info('main line')
    # 共有メモリの準備
    shmem = Value(Point, 0)
    shmem.preparingRestart = False
    shmem.relyStation = False
    # モータ制御インスタンスの生成
    motorController = MotorController()
    # 画像処理インスタンスの生成
    imageProcessing = ImageProcessing()
    # 慣性計測インスタンスの生成
    imu = Imu()
    # スタート時に一度ジャイロセンサの補正をしておく
    imu.calibrate()
    # websocketサーバの生成
    # server = Server(9001)

    p_motorContl = Process(target=motorController.target, args=(shmem,))
    p_imageProcessing = Process(target=imageProcessing.target, args=(shmem,))
    p_imu = Process(target=imu.target, args=(shmem,))
    # p_server = Process(target=server.target, args=())
    
    p_motorContl.start()
    DEBUG('p_motorContl started')
    p_imageProcessing.start()
    DEBUG('p_imageProcessing started')
    p_imu.start()
    DEBUG('p_imu started')
    # p_server.start()
    # DEBUG('p_server started')

    p_motorContl.join()
    p_imageProcessing.join()
    p_imu.join()
    # p_server.join()
