#-*- cording: utf-8 -*-

from mutagen.mp3 import MP3 as mp3
import pygame.mixer
import time

# mixerモジュールの初期化
pygame.mixer.init()
# 音楽ファイルの読み込み
pygame.mixer.music.load("./boot.mp3")
mp3_length = mp3("./boot.mp3").info.length
# 音楽再生、および再生回数の設定(-1はループ再生)
pygame.mixer.music.play(1)
time.sleep(mp3_length + 0.25) #再生開始後、音源の長さだけ待つ(0.25待つのは誤差解消)
pygame.mixer.music.stop() #音源の長さ待ったら再生停止
print('played')

