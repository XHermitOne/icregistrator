#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Версия программы/пакета.

@type MAJOR: C{int}
@var MAJOR: Мажорная часть версии

@type MINOR: C{int}
@var MINOR: Минорная часть версии

@type BUILD_IDX: C{int}
@var BUILD_IDX: Индекс сборки (всегда увеличивается автоматически при сборке пакета программы)

@type BUILD_DATE: C{string}
@var BUILD_DATE: Дата последней сборки (устанавливается автоматически)

@type BUILD_TIME: C{string}
@var BUILD_TIME: Время последней сборки (устанавливается автоматически)

@type VERSION: C{tuple}
@var VERSION: Версия (<Мажорная часть>,<Минорная часть>,<Сборка>)

@type VERSION_INFO: C{string}
@var VERSION_INFO: Расширенная информация по версии в строковом представлении
"""

import os.path
import time

__version__ = (0, 0, 1, 1)

MAJOR = 1
MINOR = 0
BUILD_IDX = 2

BUILD_DATE = '06.12.2017'
BUILD_TIME = '11:49:36'

VERSION = [MAJOR, MINOR, BUILD_IDX]

VERSION_INFO = 'icRegistrator Copyright: Alexander Kolchanov e-mail: <xhermit@ayan.ru> Version: 1.0.2 Build date: 06.12.2017 Build time: 11:49:36 '

NAME = 'icRegistrator'
COPYRIGHT = 'Alexander Kolchanov e-mail: <xhermit@ayan.ru>'


def _writeParam(sName,OldValue,NewValue):
    """
    Записать параметр в модуле.
    @param sName: Имя параметра.
    @param OldValue: Старое значение параметра.
    @param NewValue: Новое значение параметра.
    """
    f = None
    filename = os.path.abspath(os.path.splitext(__file__)[0]+'.py')
    try:
        f = open(filename, 'r')
        lines = f.readlines()
        f.close()
        f = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            line_parse = [word.strip() for word in line.split('=')]
            if line_parse[0] == sName:
                if isinstance(NewValue, str):
                    lines[i] = sName+' = \''+NewValue+'\'\n'
                elif isinstance(NewValue, unicode):
                    lines[i] = sName+' = u\''+NewValue+'\'\n'
                else:
                    lines[i] = sName+' = '+str(NewValue)+'\n'

                exp = ''
                try:
                    exp = 'global '+sName+'; '+lines[i].strip()
                    exec(exp, globals(), locals())
                except:
                    print('ERROR. Exec expression:', exp)
                    raise
                    
        txt = ''.join(lines)
        
        f = open(filename, 'w')
        f.write(txt)
        f.close()
    except:
        if f:
            f.close()
            f = None
        raise


def incBuild():
    """
    Увеличить на 1 индекс сборки.
    """
    global BUILD_IDX
    _writeParam('BUILD_IDX', BUILD_IDX, BUILD_IDX+1)


def setBuildDate(dDate, sFmt='%d.%m.%Y'):
    """
    Установить дату сборки по формату.
    """
    global BUILD_DATE
    date_str = time.strftime(sFmt, dDate)
    _writeParam('BUILD_DATE', BUILD_DATE, date_str)


def setBuildTime(tTime, sFmt='%H:%M:%S'):
    """
    Установить время сборки по формату.
    """
    global BUILD_TIME
    time_str = time.strftime(sFmt, tTime)
    _writeParam('BUILD_TIME', BUILD_TIME, time_str)


def setNowBuildDate():
    """
    Установить текущую дату сборки.
    """
    setBuildDate(time.localtime(time.time()))


def setNowBuildTime():
    """
    Установить текущее время сборки.
    """
    setBuildTime(time.localtime(time.time()))


def setVersionInfo():
    """
    Заполнить ионформацию о версии по текущим параметрам.
    """
    global NAME
    global COPYRIGHT
    global BUILD_DATE
    global BUILD_TIME
    global VERSION
    global VERSION_INFO
    
    info = ''
    if NAME:
        info += str(NAME)+' '
        
    if COPYRIGHT:
        info += 'Copyright: '+str(COPYRIGHT)+' '
    
    VERSION = [MAJOR, MINOR, BUILD_IDX]
    info += 'Version: '+'.'.join([str(v) for v in VERSION])+' '
    
    if BUILD_DATE:
        info += 'Build date: '+str(BUILD_DATE)+' '
    if BUILD_TIME:
        info += 'Build time: '+str(BUILD_TIME)+' '
        
    _writeParam('VERSION_INFO', VERSION_INFO, info)


def printVersion():
    global VERSION_INFO
    print(VERSION_INFO)    


def update():
    """
    Функция обновления параметров.
    """
    print('VERSION File:', __file__)
    incBuild()
    setNowBuildDate()
    setNowBuildTime()
    setVersionInfo()
    
    del_version_pyc()


def del_version_pyc():
    """
    Удалить version.pyc файл.
    """
    pyc_filename = os.path.abspath(os.path.splitext(__file__)[0]+'.pyc')
    if os.path.exists(pyc_filename):
        os.remove(pyc_filename)
        return True
    else:
        print('WARNING. version.py File %s not exists' % pyc_filename)
        return False


if __name__ == '__main__':
    printVersion()
