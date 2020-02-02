import FaBo9Axis_MPU9250
import time
from madgwick_py import madgwickahrs

"""

mpu9250 module test program

"""

if __name__ == '__main__':
  mpu9250 = FaBo9Axis_MPU9250.MPU9250()
  madgwick = madgwickahrs.MadgwickAHRS()

  while True:
    accel = mpu9250.readAccel()
    print('accel:' + str(accel))
    gyro = mpu9250.readGyro()
    print('gyro:' + str(gyro))
    magnet = mpu9250.readMagnet()
    print('magnet:' + str(magnet))
    if magnet["x"] is 0 and magnet["y"] is 0 and magnet["z"] is 0:
        pass
    else:
      madgwick.update((gyro["x"],gyro["y"],gyro["z"]),(accel["x"],accel["y"],accel["z"]),(magnet["x"],magnet["y"],magnet["z"]))
    print(madgwick.quaternion.to_euler_angles())
    time.sleep(1)
