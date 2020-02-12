# coding: UTF-8

from enum import IntEnum
from debug import ERROR, WARN, INFO, DEBUG, TRACE

import cv2
import numpy as np
import picamera
import picamera.array
import os
from sound import SoundPhaseE

from math import atan2, degrees, hypot


class ImageProcessing:
    # 画像出力の有効無効
    ENABLE = 1
    DISABLE = 0
    DEBUG_IMSHOW = ENABLE

    # マスクパラメータはあんまり厳しくしすぎると、本番で認識しないという事態になりそうで怖い
    RED_HSV_RANGE_MIN_1 = [0, 130, 30]
    RED_HSV_RANGE_MAX_1 = [2, 255, 255]
    RED_HSV_RANGE_MIN_2 = [160, 130, 30]
    RED_HSV_RANGE_MAX_2 = [179, 255, 255]
    BLUE_HSV_RANGE_MIN = [100, 130, 30]
    BLUE_HSV_RANGE_MAX = [150, 255, 255]
    YELLOW_HSV_RANGE_MIN = [15, 127, 30]
    YELLOW_HSV_RANGE_MAX = [30, 255, 255]

    CAMERA_CENTER_CX = 240
    CAMERA_CENTER_CY = 240
    
    # 色認識において、これ以下の面積の結果は無視する
    IGNORE_AREA_SIZE_BALL = 1000
    IGNORE_AREA_SIZE_YELLOW = 1000

    # @brief コンスタラクタ
    # @detail 初期化処理を行う
    def __init__(self):
        TRACE('ImageProcessing generated')
    
    # @brief 指定色の最大領域を検知する
    # @param hsv_img HSV変換後の処理対象画像
    # @param color_name 検知する色の名前
    # @detail
    def colorDetect2(self, hsv_img, color_name):

        if color_name == 'RED':
            # 赤色のHSVの値域1
            hsv_range_min = self.RED_HSV_RANGE_MIN_1
            hsv_range_max = self.RED_HSV_RANGE_MAX_1
            mask1 = cv2.inRange(hsv_img, np.array(hsv_range_min), np.array(hsv_range_max))

            # 赤色のHSVの値域2
            hsv_range_min = self.RED_HSV_RANGE_MIN_2
            hsv_range_max = self.RED_HSV_RANGE_MAX_2
            mask2 = cv2.inRange(hsv_img, np.array(hsv_range_min), np.array(hsv_range_max))
            mask = mask1 + mask2
        elif color_name == 'YELLOW':
            hsv_range_min = self.YELLOW_HSV_RANGE_MIN
            hsv_range_max = self.YELLOW_HSV_RANGE_MAX
            mask = cv2.inRange(hsv_img, np.array(hsv_range_min), np.array(hsv_range_max))
        elif color_name == 'BLUE':
            hsv_range_min = self.BLUE_HSV_RANGE_MIN
            hsv_range_max = self.BLUE_HSV_RANGE_MAX
            mask = cv2.inRange(hsv_img, np.array(hsv_range_min), np.array(hsv_range_max))
            
        if self.DEBUG_IMSHOW == self.ENABLE:
            cv2.imshow('Mask' + color_name, cv2.flip(mask, -1))

        _, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if color_name == 'RED' or color_name == 'BLUE':
            convex_hull_list = []
            for contour in contours:
                approx = cv2.convexHull(contour)

                M = cv2.moments(approx)
                convex_hull_list.append({'approx': approx, 'moment': M})

            if len(convex_hull_list) > 0:
                max_convex_hull = max(convex_hull_list, key=(lambda x: x['moment']['m00']))
                if max_convex_hull['moment']['m00'] > 0:
                    area_size = max_convex_hull['moment']['m00']

                    cx = int(max_convex_hull['moment']['m10'] / max_convex_hull['moment']['m00'])
                    cy = int(max_convex_hull['moment']['m01'] / max_convex_hull['moment']['m00'])

                    return cx, cy, area_size, max_convex_hull['approx']
                return -1, -1, 0.0, []
            else:
                return -1, -1, 0.0, []
        elif color_name == 'YELLOW':
            convex_hull_list = []
            for contour in contours:
                approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
                # 四角形に近い形のみ扱う
                if 3 < len(approx) < 10:
                    M = cv2.moments(approx)
                    convex_hull_list.append({'approx': approx, 'moment': M})

            if len(convex_hull_list) > 0:
                max_convex_hull = max(convex_hull_list, key=(lambda x: x['moment']['m00']))
                if max_convex_hull['moment']['m00'] > 0:
                    area_size = max_convex_hull['moment']['m00']

                    cx = int(max_convex_hull['moment']['m10'] / max_convex_hull['moment']['m00'])
                    cy = int(max_convex_hull['moment']['m01'] / max_convex_hull['moment']['m00'])

                    return cx, cy, area_size, max_convex_hull['approx']
                return -1, -1, 0.0, []
            else:
                return -1, -1, 0.0, []

    # @brief 十字マーカーを描画する
    # @param x 十字マーカーのx座標
    # @param y 十字マーカーのy座標
    # @param marker_color 十字マーカーの色
    def draw_marker(self, img, x, y, marker_color):
        cv2.line(img, (x - 7, y), (x + 7, y), color=(255, 255, 255), thickness=2)
        cv2.line(img, (x, y - 7), (x, y + 7), color=(255, 255, 255), thickness=2)
        cv2.line(img, (x - 7, y), (x + 7, y), color=marker_color, thickness=1)
        cv2.line(img, (x, y - 7), (x, y + 7), color=marker_color, thickness=1)

    # @brief 画像処理によって検知した領域からボールの方向と距離を計算する
    # @param cx 領域のx座標
    # @param cy 領域のy座標
    # @param area_size 領域の面積
    def calcBallDirection(self, cx, cy):
        ball_angle = cx - self.CAMERA_CENTER_CX
        ball_distance = cy
        
        return int(ball_angle), int(ball_distance)

    def imageProcessingFrame(self, frame, shmem):
        # HSV色空間に変換
        hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        cv2.line(frame, (self.CAMERA_CENTER_CX, 0), (self.CAMERA_CENTER_CX, 480),
                 (0, 0, 255), thickness=1)
        cv2.line(frame, (0, self.CAMERA_CENTER_CY), (480, self.CAMERA_CENTER_CY),
                 (0, 0, 255), thickness=1)

        # 赤色領域の検知
        red_cx, red_cy, red_area_size, red_convex = self.colorDetect2(hsv_img, 'RED')
        if red_cx > -1:
            self.draw_marker(frame, red_cx, red_cy, (255, 30, 30))
        
        # 黄色領域の検知
        yellow_cx, yellow_cy, yellow_area_size, yellow_convex = self.colorDetect2(hsv_img, 'YELLOW')
        if yellow_cx > -1:
            self.draw_marker(frame, yellow_cx, yellow_cy, (30, 255, 255))

        # 青色領域の検知
        blue_cx, blue_cy, blue_area_size, blue_convex = self.colorDetect2(hsv_img, 'BLUE')
        if blue_cx > -1:
            self.draw_marker(frame, blue_cx, blue_cy, (30, 30, 255))
        
        INFO('RedSize :' + str(red_area_size).rjust(8))
        INFO('YellowSize :' + str(yellow_area_size).rjust(8))
        INFO('BlueSize :' + str(blue_area_size).rjust(8))

        # 認識できた部分の面積が小さい場合は結果を無視し、distanceに不正な値を入れる
        if red_area_size > blue_area_size and red_area_size > self.IGNORE_AREA_SIZE_BALL:
            DEBUG('use RED area')
            shmem.soundPhase = SoundPhaseE.DETECT_RED_BALL
            ball_angle, ball_distance = self.calcBallDirection(red_cx, red_cy)
        elif blue_area_size > self.IGNORE_AREA_SIZE_BALL:
            DEBUG('use BLUE area')
            shmem.soundPhase = SoundPhaseE.DETECT_BLUE_BALL
            ball_angle, ball_distance = self.calcBallDirection(blue_cx, blue_cy)
        else:
            ball_angle = 0
            ball_distance = -1
        if yellow_area_size > self.IGNORE_AREA_SIZE_YELLOW:
            station_angle, station_distance = self.calcBallDirection(yellow_cx, yellow_cy)
        else:
            station_angle = 0
            station_distance = -1

        return ball_angle, ball_distance, station_angle, station_distance

    # @brief 画像処理のmain処理
    # @param shmem 共有メモリ
    def imageProcessingMain(self, shmem):
        # 画像処理を行う

        with picamera.PiCamera() as camera:
            with picamera.array.PiRGBArray(camera) as stream:
                camera.resolution = (480, 480)
                cap = cv2.VideoCapture(0)

                while cap.isOpened():
                    # 画像を取得し、stream.arrayにRGBの順で映像データを格納
                    camera.capture(stream, 'bgr', use_video_port=True)

                    ball_angle, ball_distance, station_angle, station_distance = self.imageProcessingFrame(stream.array, shmem)

                    DEBUG('ball: angle =' + str(ball_angle).rjust(5) + ', distance = ' + str(ball_distance).rjust(5))
                    DEBUG('station: angle =' + str(station_angle).rjust(5) + ', distance = ' + str(station_distance).rjust(5))
                    
                    # 結果表示
                    # 画角の前後左右と画像表示の上下左右を揃えるために画像を転置する。
                    if self.DEBUG_IMSHOW == self.ENABLE:
                        cv2.imshow('Frame', cv2.flip(stream.array, -1))
                        cv2.moveWindow('Frame', 0, 30)
                        cv2.moveWindow('MaskRED', 482, 30)
                        cv2.moveWindow('MaskYELLOW', 964, 30)
              
                    # 共有メモリに書き込む
                    shmem.ballAngle = int(ball_angle * 90 / 240)
                    shmem.ballDis = int(ball_distance)
                    shmem.stationAngle = int(station_angle * 90 / 240)
                    shmem.stationDis = int(station_distance)

                    # "q"でウィンドウを閉じる
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                    # streamをリセット
                    stream.seek(0)
                    stream.truncate()
                cv2.destroyAllWindows()

    def target(self, shmem):
        TRACE('imageProcessingMain target() start')
        self.imageProcessingMain(shmem)

    def close():
        pass
