# coding: UTF-8

import time
from enum import IntEnum
import subprocess
from debug import DEBUG, TRACE


class SoundPhaseE(IntEnum):
    FINDING_BALL = 0
    DETECT_BLUE_BALL = 1
    DETECT_RED_BALL = 2
    RECV_CAMERA_INFO = 3
    DETECT_STATION = 4
    PREPARE_RESTART = 5
    DETECT_PRESS_WALL = 6
    DETECT_YELLOW_BALL = 7
    DONE = 8


class Sound:
    def __init__(self):
        self._file_list = ['./sound/finding_ball.mp3',
                           './sound/detect_blue_ball.mp3',
                           './sound/detect_red_ball.mp3',
                           './sound/recv_camera_info.mp3',
                           './sound/detect_station.mp3',
                           './sound/prepare_restart.mp3',
                           './sound/detect_pressing_wall.mp3',
                           './sound/detect_yellow_ball.mp3',
                           './sound/done.mp3']
        TRACE('Sound generated')
    
    def update_loop(self, shmem):
        self.__play('./sound/boot.mp3')
        self._pre_phase = shmem.soundPhase
        while(True):
            now_phase = shmem.soundPhase
            if self._pre_phase != now_phase:
                self.__play(self._file_list[now_phase])
                self._pre_phase = now_phase
            time.sleep(1)
    
    def target(self, shmem):
        DEBUG('Sound target() start')
        self.update_loop(shmem)
    
    def close(self):
        pass
    
    def __play(self, file_name):
        DEBUG('play : ' + file_name)
        subprocess.call('mpg321 ' + file_name, shell=True)
        DEBUG('played : ' + file_name)
