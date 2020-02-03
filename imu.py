# coding: UTF-8

import FaBo9Axis_MPU9250
import time
from debug import DEBUG, TRACE, INFO


class Imu:
    """
    
    IMU driver class
    
    """
    
    # このセンサが一周した時の積分値
    ONE_ROUND_VALUE = 3600
    
    def __init__(self, update_interval_sec=0.1):
        TRACE('Imu generated')
        self._mpu9250 = FaBo9Axis_MPU9250.MPU9250()
        self._epsilon = 0
        self._degree = 0
        self._update_interval_sec = update_interval_sec
    
    def calibrate(self, sec=3, interval_sec=0.05):
        DEBUG('Imu.calibrate() start')
        count = int(sec / interval_sec)
        sum = 0
        for i in range(count):
            gyro = self._mpu9250.readGyro()
            sum += gyro["z"]
            time.sleep(interval_sec)
        self._epsilon = sum / count
        DEBUG('Imu epsilon = ', self._epsilon)
    
    def reset(self):
        self._degree = 0
    
    # 周回分を無視する
    def ignore_round(self, degree, one_round_value):
        if degree > 0:
            return degree % one_round_value
        else:
            return -(-degree % one_round_value)
    
    # 無駄に半周以上しないように角度を調整
    def compress_degree_in_180(self, degree, one_round_value):
        """
        
        Note:
            ignore_round()で周回分を丸めてから本関数を呼ぶこと
        
        """
        if abs(degree) > (one_round_value / 2):
            return degree - (degree / abs(degree) * one_round_value)
        return degree
    
    def calc_shortcut_degree(self, degree, one_round_value):
        return self.compress_degree_in_180(self.ignore_round(degree, one_round_value), one_round_value)
    
    def update_loop(self, shmem):
        while 1:
            # どうやら10-20秒くらいで補正値を更新しないと、ドリフトの影響が無視出来なくなる
            # リスタート準備中フラグが立っていたら、他のモジュールが待っていてくれているので、補正値の調整をする
            # 補正が終わったらフラグをクリアして、他のモジュールに調整完了を知らせる
            if shmem.preparingRestart:
                INFO('calibrate IMU to prepare restart')
                self.calibrate()
                shmem.preparingRestart = False
            gyro = self._mpu9250.readGyro()
            self._degree += gyro["z"] - self._epsilon
            # 画像認識は右側正、左側負なので、そちらの挙動と合わせるために符号反転させる
            shmem.bodyAngle = -int(self.calc_shortcut_degree(self._degree, self.ONE_ROUND_VALUE))
            DEBUG('bodyAngle = ', shmem.bodyAngle)
            time.sleep(self._update_interval_sec)
    
    def print_angle(self):
        while 1:
            gyro = self._mpu9250.readGyro()
            self._degree += gyro["z"] - self._epsilon
            DEBUG('bodyAngle = ', -int(self.calc_shortcut_degree(self._degree, self.ONE_ROUND_VALUE)))
            time.sleep(self._update_interval_sec)
    
    def target(self, shmem):
        DEBUG('Imu target() start')
        self.update_loop(shmem)
    
    def close(self):
        pass
