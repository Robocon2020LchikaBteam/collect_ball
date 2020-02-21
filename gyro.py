import FaBo9Axis_MPU9250
import time

mpu9250 = FaBo9Axis_MPU9250.MPU9250()

while True:
    accel = mpu9250.readAccel()
    print('accel:' + str(accel))
    #gyro = mpu9250.readGyro()
    #print('gyro:' + str(gyro))
    #magnet = mpu9250.readMagnet()
    #print('magnet:' + str(magnet))
    time.sleep(0.1)
