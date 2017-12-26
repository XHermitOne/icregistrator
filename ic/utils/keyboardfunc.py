#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
Модуль функции работы с клавиатурой.
"""

import sys

if sys.platform.lower().startswith('win'):
    import msvcrt
elif sys.platform.lower().startswith('lin'):
    import tty
    import termios
    import select


__version__ = (0, 0, 1, 1)

# Коды клавиш
ESC_KEY = 27
ENTER_KEY = 13
SPACE_KEY = 32


def getch():
    """
    Функция получения кода нажатой клавиши с ожиданием ввода.
    Функция создавалась как кросплатформенная.
    Код взят из https://geekbrains.ru/topics/326.
    @return: Код нажатой клавиши или None если ничего не нажато.
    """
    if sys.platform.lower().startswith('win'):
        return msvcrt.getch()
    elif sys.platform.lower().startswith('lin'):
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            c = sys.stdin.read(1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        return c
    return None


def kbhit():
    """
    Определение нажата клавиша или нет.
    @return: True - нажата / False -нет.
    """
    if sys.platform.lower().startswith('win'):
        return bool(msvcrt.kbhit())
    elif sys.platform.lower().startswith('lin'):
        dr, dw, de = select.select([sys.stdin], [], [], 0)
        return dr != []


def getchAsync():
    """
    Функция получения кода нажатой клавиши с ожиданием ввода.
    Функция создавалась как кросплатформенная.
    @return: Код нажатой клавиши или None если ничего не нажато.
    """
    if sys.platform.lower().startswith('win'):
        if msvcrt.kbhit():
            return msvcrt.getch()
    elif sys.platform.lower().startswith('lin'):
        c = None
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            if kbhit():
                c = sys.stdin.read(1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        return c

    return None


def same_key(ch, key_code):
    """
    Проверка соответствия символа коду клавиши.
    @param ch: Символ.
    @param key_code: Код клавиши.
    @return: True - соответствует / False - не соответствует.
    """
    return (ord(ch) == key_code) if isinstance(ch, str) or isinstance(ch, unicode) else False


if __name__ == '__main__':
    import time
    start_time = time.time()
    while (time.time() - start_time) < 10:
        ch_key = getchAsync()
        if ch_key:
            print(ord(ch_key))
