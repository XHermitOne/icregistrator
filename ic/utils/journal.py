#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Функции поддержки ведения простого файлового журнала.
Используется для журналирования сообщений прикладного уровня.
Такие журналы необходимы для диагностики отказов прикладной системы.
"""

import datetime
from . import log
from . import txtfunc
# from ic.utils import ic_str

__version__ = (0, 0, 1, 1)

LOG_FILENAME = None
IS_DATETIME = True
IS_PRINT = False
LOG_ENCODING = None


def init(sLogFileName, bDateTime=True, bPrint=False,
         sEncoding=log.DEFAULT_ENCODING):
    """
    Инициализация файла журнала.
    @param sLogFileName: Полное имя файла журнала.
    @param bDateTime: Добавить автоматическое добавление времени регистрации к сообщению?
    @param bPrint: Дублировать сообщение в консоли?
        Все сообщения в таком случае отображаются с цветом purple.
    @param sEncoding: Кодовая страница журнала.
    @return: True/False.
    """
    globals()['LOG_FILENAME'] = sLogFileName
    globals()['IS_DATETIME'] = bDateTime
    globals()['IS_PRINT'] = bPrint
    globals()['LOG_ENCODING'] = sEncoding


def write_msg(sMessage):
    """
    Записать сообщение в журнал.
    @param sMessage: Текст сообщения.
    @return: True/False.
    """
    log_filename = globals()['LOG_FILENAME']
    is_datetime = globals()['IS_DATETIME']
    is_print = globals()['IS_PRINT']
    log_encoding = globals()['LOG_ENCODING']

    if is_print:
        log.print_color_txt(sMessage, sColor=log.PURPLE_COLOR_TEXT)

    if is_datetime:
        now = datetime.datetime.now()
        sMessage = u'%s %s' % (now.strftime(log.LOG_DATETIME_FMT), sMessage)

    try:
        msg = sMessage.encode(log_encoding)
    except:
        log.fatal(u'Ошибка преобразования сообщения к текстовому виду. Кодовая страница <%s>' % log_encoding)
        msg = ''
    return txtfunc.text_file_append(log_filename, msg)
