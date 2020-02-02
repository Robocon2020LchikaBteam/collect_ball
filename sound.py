# coding: UTF-8

import time
from enum import Enum
import subprocess
from debug import DEBUG, TRACE


class SoundPhaseE(Enum):
    FINDING_BALL = 0
    DETECT_BLUE_BALL = 1
    DETECT_RED_BALL = 2
    RECV_CAMERA_INFO = 3
    DETECT_STATION = 4


class Sound:
    def __init__(self):
        TRACE('Sound generated')
    
    def update_loop(self, shmem):
        self.__play('./sound/boot.mp3')
        while(True):
            time.sleep(1)
            pass
    
    def target(self, shmem):
        DEBUG('Sound target() start')
        self.update_loop(shmem)
    
    def close(self):
        pass
    
    def __play(self, file_name):
        DEBUG('play : ' + file_name)
        subprocess.call('mpg321 ' + file_name, shell=True)
        DEBUG('played : ' + file_name)
