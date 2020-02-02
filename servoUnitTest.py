from servo import Servo
import time

"""

test program for servo driver

"""

if __name__ == "__main__":
    servo = Servo(4)
    servo.write(12, 5, 0.1)
    time.sleep(3)
    servo.write(7.25, 5, 0.1)
