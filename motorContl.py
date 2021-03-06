# coding: UTF-8

import time
from enum import Enum
from debug import ERROR, INFO, DEBUG, TRACE
from miniMotorDriver import MiniMotorDriver
from servo import Servo
from gp2y0e import Gp2y0e
import json
from sound import SoundPhaseE

"""

motor controle module

"""


# 状態用列挙型
class MotionStateE(Enum):
    CHASE_BALL = 0
    GO_TO_STATION = 1
    PREPARE_RESTART = 2


# モータ制御用クラス
class MotorController:
    # 移動アルゴリズム切り替え用変数
    DEBUG_CHASE_ALGORITHM = 1

    # モータ制御用パラメータ群
    # ボールとの角度からモータ速度変換時の補正値
    CORRECTION_VALUE_BALL_ANGLE_TO_SPEED = 3
    # ボールとの距離からモータ速度変換時の補正値
    CORRECTION_VALUE_DISTANCE_TO_SPEED = 100
    # 距離センサの値がinfinityの時のモータの値
    SPEED_DISTANCE_INFINITE = 25
    # ボールが正面にある時のモータの値(距離センサを使わない場合のみ使用)
    SPEED_FRONT_BALL = 30
    # どうしようもない時用の値(ゆっくり旋回)
    SPEED_NOTHING_TO_DO = 5, -5
    # 停止
    SPEED_STOP = 0, 0
    # 首振りモード時旋回パラメータ
    SPEED_SWING_ROTATE = 100, -100
    # 後退用モータ値(主にスタック回避周りで使用する)
    SPEED_BACK = 30
    # ボール保持判定用距離[cm]
    DISTANCE_HAVE_BALL = 15
    # スタック判定用距離[cm]
    DISTANCE_STUCK = 5
    # 壁スタック判定用時間[s]
    # この時間以上継続して壁が検出されていたら壁にハマっていると判断して何らかの対処をする
    TIME_WALL_STUCK = 3

    # 移動アルゴリズム1, 2で使用
    # ボール追跡時の基準スピード
    SPEED_CHASE = 45
    # ボール追跡時の比例項の係数
    K_CHASE_ANGLE = 0.6  # SPEED_CHASE / 180にするとよい？
    # ステーション指示に従う際の基準スピード
    SPEED_STATION_GUIDE = 10
    # ステーション指示に従う際の比例項の係数
    K_STATION_GUIDE_ANGLE = 0.15  # SPEED_CHASE / 180にするとよい？
    # 再スタート準備時の基準スピード
    SPEED_TURN = 20
    # 再スタート準備時の比例項の係数
    K_TURN_ANGLE = 1.5

    # コンストラクタ
    def __init__(self):
        DEBUG('MotorController generated')
        # インスタンス変数初期化
        # ドリブル状態に入ったかを記憶する変数
        self.is_dribble_started = False
        # モータ制御後処理インスタンス生成
        self.motorControlPostProcessor = MotorControlPostProcessor()
        self.motorControlPostProcessor.enable_escape_press_wall(speed=MotorController.SPEED_BACK)
        # 距離センサ用インスタンス生成
        self.distanceSensor = Gp2y0e(0x40)
        # モータドライバ制御用インスタンス生成
        self.left_motor = MiniMotorDriver(0x65)
        self.right_motor = MiniMotorDriver(0x60)
        self.servo = Servo(0x41)
        self.servo.up()
        # ボール追跡モード管理用インスタンス生成
        self.chaseBallMode = ChaseMode()
        # 動作状態初期化
        self.motion_status = MotionStateE.CHASE_BALL
        # 壁付近走行中かどうか保持用変数初期化
        self._is_near_wall = False
        self._near_wall_start_time = time.time()

    # 数値の絶対値を100に丸める
    def roundOffWithin100(self, num):
        if abs(num) > 100:
            return num / abs(num) * 100
        else:
            return num
    
    # 数値を100に丸めた際の差分を取得する
    def calcDiffRondOffWithin100(self, num):
        if abs(num) > 100:
            return (num / abs(num) * 100) - num
        else:
            return 0
    
    # モータ値の絶対値を100に丸めつつ
    # 丸められていない方を丸められた方の値に応じて修正する
    def roundOffMotorSpeeds(self, motorSpeeds):
        # モータ値それぞれについて絶対値を100に丸めた時の差分
        diffPower = [0, 0]
        diffPower[0] = self.calcDiffRondOffWithin100(motorSpeeds[0])
        diffPower[1] = self.calcDiffRondOffWithin100(motorSpeeds[1])
        DEBUG('diffPower =', diffPower[0], ', ', diffPower[1])

        returnSpeeds = self.roundOffWithin100(motorSpeeds[0]), self.roundOffWithin100(motorSpeeds[1])
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

    # ボール情報を使ってモータの値を計算する
    def calcMotorPowersByBallAngleAndDis(self, ballAngle, ballDis):
        if self.DEBUG_CHASE_ALGORITHM == 0:
            # ボールが正面にある場合
            if ballAngle == 0:
                TRACE('calcMotor patern : ballAngle = 0')
                # 距離センサの値をボールまでの距離としてモータの値を計算
                return self.getMotorPowerByDistance(ballDis)
            # ボールが正面にない場合
            else:
                TRACE('calcMotor patern : boalAngle != 0')
                # モータの値は補正をかける
                speed = ballAngle / MotorController.CORRECTION_VALUE_BALL_ANGLE_TO_SPEED
                # 絶対値が100を超える場合は100に丸める
                #speed = self.roundOffWithin100(speed)
                # debug
                speed = speed / abs(speed) * 5
                return (-speed), speed
        if self.DEBUG_CHASE_ALGORITHM == 1:
            # P制御
            return MotorController.SPEED_CHASE - MotorController.K_CHASE_ANGLE * ballAngle, \
                MotorController.SPEED_CHASE + MotorController.K_CHASE_ANGLE * ballAngle

    # ボールとの角度のみを使ってモータの値を計算する
    def calcMotorPowersByBallAngle(self, ballAngle, speed, k):
        if self.DEBUG_CHASE_ALGORITHM == 0:
            # ボールが正面にある場合
            if ballAngle == 0:
                TRACE('calcMotor patern : ballAngle = 0')
                # モータの値は固定値で前進
                return MotorController.SPEED_FRONT_BALL, MotorController.SPEED_FRONT_BALL
            # ボールが正面にない場合
            else:
                TRACE('calcMotor patern : boalAngle != 0')
                # モータの値は補正をかける
                speed = ballAngle / MotorController.CORRECTION_VALUE_BALL_ANGLE_TO_SPEED
                # left, rightの順で返却
                return speed, (-speed)
        elif self.DEBUG_CHASE_ALGORITHM == 1:
            # P制御
            return MotorController.SPEED_CHASE + MotorController.K_CHASE_ANGLE * ballAngle, \
                MotorController.SPEED_CHASE - MotorController.K_CHASE_ANGLE * ballAngle
        else:
            ERROR('Invalid Value : DEBUG_CHASE_ALGORITHM =', self.DEBUG_CHASE_ALGORITHM)
            return MotorController.SPEED_STOP
    
    # モータの値を計算する
    def calcMotorPowers(self, shmem, motion_status):
        # 現在の状態に応じて追跡対象を変える
        if motion_status == MotionStateE.CHASE_BALL:
            TRACE('motion_status = CHASE_BALL')
            if shmem.ballDis != -1:
                return self.calcMotorPowersByBallAngle(shmem.ballAngle, MotorController.SPEED_CHASE, MotorController.K_CHASE_ANGLE)
            TRACE('shmem.ballDis is invalid value')
            if self.chaseBallMode.now() == ChaseMode.NORMAL:
                TRACE('chaseBallMode = NORMAL')
                return self.calcMotorPowersByBallAngle(shmem.bodyAngle / 10, MotorController.SPEED_CHASE, MotorController.K_CHASE_ANGLE)
            # ボールが視界になくて、首振りモードの時はボールを見つけるためにとりあえず旋回する
            DEBUG('chaseBallMode = SWING')
            return MotorController.SPEED_SWING_ROTATE
        elif motion_status == MotionStateE.GO_TO_STATION:
            TRACE('motion_status = GO_TO_STATION')
            if shmem.stationDis != -1:
                shmem.soundPhase = SoundPhaseE.DETECT_STATION
                return self.calcMotorPowersByBallAngle(shmem.stationAngle, MotorController.SPEED_CHASE, MotorController.K_CHASE_ANGLE)
            TRACE('shmem.ballDis is invalid value')
            # センターカメラから指令が来ていたらguide_info.jsonに有効な値が入っている
            with open('./guide_info.json', mode='r') as f:
                try:
                    guide_info_json = json.load(f)
                    guide_degree = guide_info_json.get('degree', 360)
                    if guide_degree != 360:
                        shmem.soundPhase = SoundPhaseE.RECV_CAMERA_INFO
                        DEBUG('guide_degree = ' + str(guide_degree))
                        # センターから停止命令が来ていたらモータ止める
                        if guide_info_json.get('wait', False):
                            DEBUG('recieved stop order!')
                            return 0, 0
                        return self.calcMotorPowersByBallAngle(-guide_degree, MotorController.SPEED_STATION_GUIDE,
                                                               MotorController.K_STATION_GUIDE_ANGLE)
                except json.JSONDecodeError:
                    ERROR('faild to load guide_info.json')
            body_angle = shmem.bodyAngle
            return self.calcMotorPowersByBallAngle(body_angle / 10 - (body_angle / abs(body_angle) * 180), MotorController.SPEED_CHASE,
                                                   MotorController.K_CHASE_ANGLE)
        # PREPARE_RETART
        TRACE('motion_status = PREPARE_RESTART')
        return (0, 0)
        # return self.calcMotorPowersByBallAngle(shmem.stationAngle)
    
    def prepare_restart(self, shmem):
        self.left_motor.drive(-50)
        self.right_motor.drive(-50)
        time.sleep(1)
        while True:
            angle = shmem.bodyAngle / 10
            if abs(angle) < 30:
                break
            self.left_motor.drive(MotorController.SPEED_TURN + MotorController.K_TURN_ANGLE * angle)
            self.right_motor.drive(-MotorController.SPEED_TURN - MotorController.K_TURN_ANGLE * angle)
            time.sleep(0.1)
    
    def is_going_into_corner(self, wall_size):
        if wall_size == -1:
            self._is_near_wall = False
            return False
        else:
            if self._is_near_wall:
                if time.time() - self._near_wall_start_time > MotorController.TIME_WALL_STUCK:
                    INFO('### going into corner now')
                    return True
                return False
            else:
                DEBUG('### detect near wall start')
                self._near_wall_start_time = time.time()
                self._is_near_wall = True
        return False
    
    def escape_from_corner(self, shmem):
        shmem.soundPhase = SoundPhaseE.DETECT_PRESS_WALL
        INFO('### escape from corner')
        self.left_motor.drive(-MotorController.SPEED_BACK)
        self.right_motor.drive(-MotorController.SPEED_BACK)
        time.sleep(2)
        if shmem.wallX > 0:
            self.left_motor.drive(-100)
            self.right_motor.drive(100)
        else:
            self.left_motor.drive(100)
            self.right_motor.drive(-100)
        time.sleep(1)
        self.left_motor.drive(MotorController.SPEED_CHASE)
        self.right_motor.drive(MotorController.SPEED_CHASE)
        time.sleep(3)
    
    # モータの値を計算しドライバへ送る
    def calcAndSendMotorPowers(self, shmem):
        self.chaseBallMode.set_mode(ChaseMode.NORMAL)
        while 1:
            if self.motion_status == MotionStateE.CHASE_BALL:
                # ボール捕獲に移る
                if 100 < shmem.ballDis < 160 and -20 < shmem.ballAngle < 20:
                    INFO('capture ball')
                    self.left_motor.drive(0)
                    self.right_motor.drive(0)
                    self.servo.down()
                    time.sleep(1)
                    self.motion_status = MotionStateE.GO_TO_STATION
            elif self.motion_status == MotionStateE.GO_TO_STATION:
                distanceSensorValue = self.distanceSensor.read()
                DEBUG('distanceSensor = ' + str(distanceSensorValue))
                # ボール消失してる
                if distanceSensorValue > MotorController.DISTANCE_HAVE_BALL:
                    INFO('lost ball')
                    self.left_motor.drive(0)
                    self.right_motor.drive(0)
                    self.servo.up()
                    # ステーションが見えている場合はステーションにボールを渡せたと判断して再スタートする
                    if shmem.stationDis != -1:
                        shmem.soundPhase = SoundPhaseE.DONE
                        INFO('lost ball -> in station')
                        self.chaseBallMode.set_mode(ChaseMode.NORMAL)
                        self.motion_status = MotionStateE.PREPARE_RESTART
                    self.motion_status = MotionStateE.CHASE_BALL
                # TODO: ステーション到着後の動き
                if 200 < shmem.stationDis < 310:
                    INFO('reached station')
                    self.left_motor.drive(0)
                    self.right_motor.drive(0)
                    self.servo.up()
                    # ステーションに向かっている間に追跡モードがどうなっているか分からないので、通常にリセットしておく
                    shmem.soundPhase = SoundPhaseE.DONE
                    self.chaseBallMode.set_mode(ChaseMode.NORMAL)
                    self.motion_status = MotionStateE.PREPARE_RESTART
            elif self.motion_status == MotionStateE.PREPARE_RESTART:
                INFO('PREPARE RESTART start')
                self.left_motor.drive(0)
                self.right_motor.drive(0)
                shmem.preparingRestart = True
                shmem.soundPhase = SoundPhaseE.PREPARE_RESTART
                while(shmem.preparingRestart):
                    time.sleep(0.1)
                self.prepare_restart(shmem)
                self.chaseBallMode.set_mode(ChaseMode.NORMAL)
                INFO('PREPARE RESTART end -> CHASE BALL')
                self.motion_status = MotionStateE.CHASE_BALL
                continue
                    
            # モータ値計算
            motorPowers = self.calcMotorPowers(shmem, self.motion_status)
            # モーター値後処理(現在は首振り検知処理のみ)
            # motorPowers = self.motorControlPostProcessor.escapeSwing(motorPowers)
            # ステーションに戻るとき隅っこにハマる場合があるので、その時は中央に戻ることを試みる
            if self.motion_status == MotionStateE.GO_TO_STATION and self.is_going_into_corner(shmem.wallSize):
                self.escape_from_corner(shmem)
            motorPowers = self.motorControlPostProcessor.run(motorPowers, shmem.bodyAngle / 10)
            # ボール保持中じゃないのに前方近くに何かあったら後退して回避する
            if self.servo.is_lifting() and self.distanceSensor.read() < MotorController.DISTANCE_STUCK:
                INFO('### detect something barrier')
                motorPowers = (-MotorController.SPEED_BACK, -MotorController.SPEED_BACK)
            # モータ値を正常値にまるめる
            motorPowers = self.roundOffMotorSpeeds(motorPowers)
            # モータ値送信
            self.left_motor.drive(motorPowers[0])
            self.right_motor.drive(motorPowers[1])
            # とりあえず一定時間間隔で動かす
            INFO('motor r=' + str(motorPowers[0]).rjust(4) + ', l=' + str(motorPowers[1]).rjust(4),
                 ',ball angle, distance=' + str(shmem.ballAngle).rjust(4) + ',' + str(shmem.ballDis).rjust(4),
                 ',station angle, distance=' + str(shmem.stationAngle).rjust(4) + ',' + str(shmem.stationDis).rjust(4),
                 ',body angle=' + str(shmem.bodyAngle / 10).rjust(4),
                 )
            time.sleep(0.1)
    
    # 起動処理
    def target(self, shmem):
        DEBUG('MotorController target() start')
        self.calcAndSendMotorPowers(shmem)

    # 停止処理(仮)
    def close():
        pass


class MotorControlPostProcessor:
    # モータ制御後処理パラメータ群
    # 首振り検知方向転換間隔閾値[s]、この時間以内に方向転換を繰り返すと首振りと検知する
    THRESHOLD_TIME_SWING_DETECT = 2
    # 首振り検知方向転換回数閾値、この回数以上方向転換を繰り返すと首振りと検知する
    THRESHOLD_COUNT_SWING_DETECT = 3
    # 首振り回避時間[s]、首振り検知したらこの時間分直進する
    TIME_ESCAPE_FROM_SWING = 1
    # 首振り回避の際のモータの値
    SPEED_ESCAPE_FROM_SWING = 5, 5

    def __init__(self):
        # 前回モータ値
        self.pre_motor_powers = 0, 0
        # 前回方向転換時刻(首振り検知用)
        self.pre_direction_change_time = time.time()
        # 首振り検知用方向転換数
        self.count_direction_change_detect_swing = 0
        # 首振り回避状態
        self.is_escaping_swing = False
        # 首振り回避開始時刻
        self.escape_swing_start_time = time.time()
        self._is_escape_press_wall = False
        TRACE('MotorControlPostProcessor generated')
    
    def run(self, motorPowers, bodyAngle):
        if self._is_escape_press_wall:
            motorPowers = self.__escape_press_wall(motorPowers, bodyAngle)
        self._pw_pre_power = motorPowers
        self._pw_pre_body_angle = bodyAngle
        return motorPowers
    
    # TODO: スタック回避処理を別クラスにする
    def enable_escape_press_wall(self, error_count=10, diff_angle=3, back_time=2, speed=30):
        if self._is_escape_press_wall:
            return False
        self._pw_error_count_limit = error_count
        self._pw_error_count_now = 0
        self._pw_diff_angle = diff_angle
        self._pw_back_time = back_time
        self._pw_speed = speed
        self._is_escape_press_wall = True
        self._pw_pre_power = (0, 0)
        self._pw_pre_body_angle = 9999
        self._pw_start_back_time = time.time()
        self._pw_enable_force_back = False
        return True
    
    def disable_escape_press_wall(self):
        self._is_escape_press_wall = False
    
    def __escape_press_wall(self, motorPowers, bodyAngle):
        # すでにバック中の場合
        if self._pw_enable_force_back:
            if (time.time() - self._pw_start_back_time) > self._pw_back_time:
                DEBUG('### END back for escape press wall')
                self._pw_enable_force_back = False
                # 壁押し付け状態判定用変数初期化
                self._pw_error_count_now = 0
            TRACE('### CONTINUE back for escape press wall')
            return -self._pw_speed, -self._pw_speed
        # 旋回しようとしているかどうか
        # TODO: このパラメータも上位側で指定可能にする
        if abs(self._pw_pre_power[0] - self._pw_pre_power[1]) > 50 and abs(self._pw_pre_body_angle - bodyAngle) < self._pw_diff_angle:
            DEBUG('### pressing wall count +1')
            self._pw_error_count_now += 1
        else:
            self._pw_error_count_now = 0
        if self._pw_error_count_now >= self._pw_error_count_limit:
            INFO('### detect pressing wall count')
            self._pw_enable_force_back = True
            self._pw_start_back_time = time.time()
            # 別にこの時はバックしなくてもいいかもしれないが一応
            return -self._pw_speed, -self._pw_speed
        return motorPowers

    def escapeSwing(self, motorPowers):
        # 首振り回避する必要がある場合
        if self.isNeedToEscapeSwing(motorPowers):
            TRACE('escape from swing')
            # 首振り回避用のモータ値を返す
            return MotorControlPostProcessor.SPEED_ESCAPE_FROM_SWING
        # 首振り回避する必要がない場合
        else:
            TRACE('not escape from swing')
            # 入力値をそのまま返す
            return motorPowers

    def isNeedToEscapeSwing(self, motorPowers):
        # すでに首振り回避状態に入っている
        if self.is_escaping_swing:
            # 首振り回避開始時からの経過時間が閾値より大きかった場合
            if (time.time() - self.escape_swing_start_time) > MotorControlPostProcessor.TIME_ESCAPE_FROM_SWING:
                # 首振り回避終了
                DEBUG('swing end')
                self.is_escaping_swing = False
                return False
            # 首振り回避開始時から十分時間が経過していない場合
            else:
                # 首振り回避継続
                return True
        # 首振り回避中でない
        else:
            # 首振り開始?
            if self.isSwingStarted(motorPowers):
                # 首振り回避開始
                DEBUG('swing start')
                self.is_escaping_swing = True
                return True
            else:
                # 首振り回避引き続き必要なし
                return False
    
    def isSwingStarted(self, motorPowers):
        # 首振り検知用方向転換数更新
        self.updateCountDerectionChangeDetectSwing(motorPowers)
        # 首振り検知用方向転換数が閾値を超えていたら
        if self.count_direction_change_detect_swing > MotorControlPostProcessor.THRESHOLD_COUNT_SWING_DETECT:
            return True
        else:
            return False
    
    def updateCountDerectionChangeDetectSwing(self, motorPowers):
        # 方向転換した場合
        if motorPowers[0] * self.pre_motor_powers[0] < 0 and motorPowers[1] * self.pre_motor_powers[1] < 0 and motorPowers[0] != motorPowers[1]:
            # 前回方向転換検知時からの経過時間が閾値より小さかった場合
            if (time.time() - self.pre_direction_change_time) > MotorControlPostProcessor.THRESHOLD_TIME_SWING_DETECT:
                TRACE('count_direction_change_detect_swing : increment')
                # 首振り検知用方向転換数をインクリメントする
                self.count_direction_change_detect_swing += 1
            # 前回方向転換検知時から十分時間が経過していた場合
            else:
                TRACE('count_direction_change_detect_swing : reset')
                # 首振り検知用方向転換数をリセット
                self.count_direction_change_detect_swing = 1
            DEBUG('count_derection_change_detect_swing = ', self.count_direction_change_detect_swing)


class ChaseMode:
    """
    
    Manage chase methods
    
    Examples:
        >>> chaseMode = ChaseMode(initial_mode)
        >>> now_chase_mode = cheseMode.now()
        >>> if now_chase_mode is HOGE:
        >>>     hoge = fuga
    
    """
    NORMAL = 0
    SWING = 1
    
    def __init__(self, max_normal_time_sec=10, max_swing_time_sec=6):
        self._mode = ChaseMode.NORMAL
        self._now_mode_start_time = time.time()
        self._MAX_NORMAL_TIME_SEC = max_normal_time_sec
        self._MAX_SWING_TIME_SEC = max_swing_time_sec
    
    def now(self):
        self.__update()
        return self._mode
    
    def set_mode(self, mode):
        self._now_mode_start_time = time.time()
        self._mode = mode
    
    def __update(self):
        if self._mode == ChaseMode.NORMAL:
            if time.time() - self._now_mode_start_time > self._MAX_NORMAL_TIME_SEC:
                self._now_mode_start_time = time.time()
                self._mode = ChaseMode.SWING
        if self._mode == ChaseMode.SWING:
            if time.time() - self._now_mode_start_time > self._MAX_SWING_TIME_SEC:
                self._now_mode_start_time = time.time()
                self._mode = ChaseMode.NORMAL
