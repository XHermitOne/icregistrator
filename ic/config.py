#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Конфигурационный файл.

Параметры:

@type DEBUG_MODE: C{bool}
@var DEBUG_MODE: Режим отладки (вкл./выкл.)

"""

import os.path
import datetime

PRJ_NAME = 'icregistrator'

PROFILE_DIR = os.path.join(os.environ.get('HOME', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')), 
                           '.%s' % PRJ_NAME)

# Файл лога
LOG_FILENAME = os.path.join(PROFILE_DIR, 
                            '%s_%s.log' % (PRJ_NAME, datetime.date.today().isoformat()))

JOURNAL_FILENAME = os.path.join(PROFILE_DIR,
                                '%s_%s.jrn' % (PRJ_NAME, datetime.date.today().isoformat()))

DEBUG_MODE = True
LOG_MODE = True

DEFAULT_INI_FILENAME = 'settings.ini'

# Файл настроек
SETTINGS_FILENAME = None

# Режимы запуска регистратора
RUN_MODE_SINGLE = 'single'
RUN_MODE_LOOP = 'loop'
RUN_MODE_SRC_DIAGNOSTIC = 'src_diagnostic'
RUN_MODE_DST_DIAGNOSTIC = 'dst_diagnostic'
RUN_MODE_DEBUG = 'debug'
RUN_MODE = RUN_MODE_DEBUG

# Список имен описаний источников данных
SOURCES = []

# Список имен описаний приемников данных
DESTINATIONS = []

# Порядок выполнения обработки объектов
# Для некоторых задач требуется выполнение операций чтения/записи
# выполнять в определенном порядке
# Если этот список не определен, то сначала обрабатывается чтение данных из всех источников
# а затем запись в получатели
QUEUE = []

# Задержка между тактами режима циклической обработки
TICK_PERIOD = 300

# Время начала текущего такта
TICK_DT_START = datetime.datetime.now()
# Время окончания текущего такта
TICK_DT_STOP = datetime.datetime.now()

# Объект движка программы
# Доступ ко всем объекта осуществляем через этот объект
ENGINE = None


def get_cfg_var(sName):
    """
    Прочитать значение переменной конфига.
    @type sName: C{string}
    @param sName: Имя переменной.
    """
    return globals()[sName]


def set_cfg_var(sName, vValue):
    """
    Установить значение переменной конфига.
    @type sName: C{string}
    @param sName: Имя переменной.
    @param vValue: Значение переменной.
    """
    globals()[sName] = vValue
