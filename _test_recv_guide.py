import json
from debug import DEBUG, ERROR, TRACE, INFO
from motorContl import MotorController
from miniMotorDriver import MiniMotorDriver
import time


# ボールとの角度のみを使ってモータの値を計算する
def calcMotorPowersByBallAngle(ballAngle):
    # P制御
    return MotorController.SPEED_CHASE + MotorController.K_CHASE_ANGLE * ballAngle, \
        MotorController.SPEED_CHASE - MotorController.K_CHASE_ANGLE * ballAngle


# 数値の絶対値を100に丸める
def roundOffWithin100(num):
    if abs(num) > 100:
        return num / abs(num) * 100
    else:
        return num


# 数値を100に丸めた際の差分を取得する
def calcDiffRondOffWithin100(num):
    if abs(num) > 100:
        return (num / abs(num) * 100) - num
    else:
        return 0


def roundOffMotorSpeeds(motorSpeeds):
    # モータ値それぞれについて絶対値を100に丸めた時の差分
    diffPower = [0, 0]
    diffPower[0] = calcDiffRondOffWithin100(motorSpeeds[0])
    diffPower[1] = calcDiffRondOffWithin100(motorSpeeds[1])
    DEBUG('diffPower =', diffPower[0], ', ', diffPower[1])

    returnSpeeds = roundOffWithin100(motorSpeeds[0]), roundOffWithin100(motorSpeeds[1])
    # 両モータ絶対値が100を超えている場合は100に丸めるのみ
    if diffPower == [0, 0]:
        TRACE('both power abs over 100')
        return returnSpeeds
    # 左モータ値のみ絶対値が100を超える
    elif diffPower[0] != 0:
        TRACE('left power abs over 100')
        # 右モータ値のみ差分分だけ調整する
        return returnSpeeds[0], returnSpeeds[1] + diffPower[0]
    # 右モータ値のみ絶対値が100を超える
    elif diffPower[1] != 0:
        TRACE('right power abs over 100')
        # 左モータ値のみ差分分だけ調整する
        return returnSpeeds[0] + diffPower[1], returnSpeeds[1]
    # どちらも絶対値がを100を超えない
    else:
        TRACE('both power abs under 100')
        return returnSpeeds


if __name__ == '__main__':
    # モータドライバ制御用インスタンス生成
    left_motor = MiniMotorDriver(0x65)
    right_motor = MiniMotorDriver(0x60)
    m1 = 0
    m2 = 0
    while(True):
        with open('./guide_info.json', mode='r') as f:
            try:
                guide_info_json = json.load(f)
                guide_degree = guide_info_json.get('degree', 360)
                if guide_degree != 360:
                    INFO('guide_degree = ' + str(guide_degree))
                    m1, m2 = calcMotorPowersByBallAngle(-guide_degree)
            except json.JSONDecodeError:
                ERROR('faild to load guide_info.json')
        
        motorPowers = roundOffMotorSpeeds((m1, m2))
        INFO('left: ' + str(motorPowers[0]) + 'right: ' + str(motorPowers[1]))
        # モータ値送信
        left_motor.drive(motorPowers[0])
        right_motor.drive(motorPowers[1])
        time.sleep(0.1)
