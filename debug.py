# -*- coding: utf8 -*-

"""
How to use

1. debug printを使用したいファイルで以下のようにimportする。

.. code-block:: python

    from debug import ERROR, WARN, INFO, DEBUG, TRACE

2. DEBUG_LEVELに、ログ出力のレベルを指定する。

| 指定したレベル以上のログが出力される。
| 例： ``DEBUG_LEVEL_INFO`` を指定すると、ERROR,WARN,INFOが出力される。

3. 使用したいlevelのdebug printを通常のprint文のように記述する。

| 複数引数にも対応している。

4. debug levelの目安

| ERROR : プレー続行不可能になるようなエラー
| WARN  : プレー続行不可能とはならないような警告
| INFO  : 他スレッドとの結合動作において表示したい情報
| DEBUG : 自スレッドのみの単体デバッグにおいて表示したい情報
| TRACE : 処理の開始終了や分岐の出入りなど、ルートを確認するための情報
"""

import datetime

DEBUG_LEVEL_OFF = -1
DEBUG_LEVEL_ERROR = 0
DEBUG_LEVEL_WARN = 1
DEBUG_LEVEL_INFO = 2
DEBUG_LEVEL_DEBUG = 3
DEBUG_LEVEL_TRACE = 4
DEBUG_LEVEL_ALL = 5

DEBUG_DISABLE = 0
DEBUG_ENABLE = 1

# ログ出力のレベルを指定
DEBUG_LEVEL = DEBUG_LEVEL_ALL


def dummyFunc(level, *args):
    pass


def debugPrint(level, *args):
    now = datetime.datetime.now()
    timestamp = ''.join(['[', now.strftime('%H:%M:%S.%f')[:-3], ']'])
    print(timestamp + level + ' ' + ' '.join(map(str, args)))


debugFuncList = [dummyFunc, dummyFunc, dummyFunc, dummyFunc, dummyFunc]

for i in range(DEBUG_LEVEL_ALL):
    if DEBUG_LEVEL >= i:
        debugFuncList[i] = debugPrint


def ERROR(*args):
    debugFuncList[DEBUG_LEVEL_ERROR]('[ERROR]', *args)


def WARN(*args):
    debugFuncList[DEBUG_LEVEL_WARN]('[WARN ]', *args)


def INFO(*args):
    debugFuncList[DEBUG_LEVEL_INFO]('[INFO ]', *args)


def DEBUG(*args):
    debugFuncList[DEBUG_LEVEL_DEBUG]('[DEBUG]', *args)


def TRACE(*args):
    debugFuncList[DEBUG_LEVEL_TRACE]('[TRACE]', *args)


if __name__ == '__main__':
    ERROR('error test')
    WARN('warn test')
    INFO('info test')
    DEBUG('debug test')
    TRACE('trace test')
