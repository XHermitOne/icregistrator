#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
Модуль дополнительных функций.
@author: Колчанов А.В. <xhermit@rambler.ru>
"""

import sys
import os
import os.path
import shutil
import datetime
import time
import random
import md5
from ic.config import *

__version__ = (0, 0, 2, 1)


def get_var(sName):
    """
    Прочитать значение переменной конфига.
    @type sName: C{string}
    @param sName: Имя переменной.
    """
    return globals()[sName]


def set_var(sName, vValue):
    """
    Установить значение переменной конфига.
    @type sName: C{string}
    @param sName: Имя переменной.
    @param vValue: Значение переменной.
    """
    globals()[sName] = vValue


def isLinuxPlatform():
    """
    ОС linux?
    """
    return sys.platform.startswith('lin')


def isWindowsPlatform():
    """
    ОС windows?
    """
    return sys.platform.startswith('win')


def getPlatform():
    """
    ОС
    """
    return sys.platform


def isDebugMode():
    """
    Режим отладки?
    """
    global DEBUG_MODE
    return DEBUG_MODE


def isLogMode():
    """
    Режим ведения журнала?
    """
    global LOG_MODE
    return LOG_MODE


def getHomeDir():
    """
    Папка HOME.
    @return: Строку-путь до папки пользователя.
    """
    if isWindowsPlatform():
        home_dir = os.environ['HOMEDRIVE']+os.environ['HOMEPATH']
        home_dir = home_dir.replace('\\', '/')
    else:
        home_dir = os.environ['HOME']
    return os.path.normpath(home_dir)


def getProfilePath():
    """
    Папка сохраненных параметров программы.
        Находиться в HOME/{{PROFILE_DIRNAME}}.
        Функция сразу провеяет если этой папки нет,
        то создает ее.
    """
    home_dir = getHomeDir()
    global PROFILE_DIRNAME
    profile_path = os.path.normpath(home_dir+'/'+PROFILE_DIRNAME)
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
    return profile_path


def getLogFileName():
    """
    Файл лога. Находиться в HOME/.sbprint.
    """
    return os.path.normpath(getProfilePath()+'/'+LOG_FILENAME)


def copyFile(sFileName, sNewFileName, bRewrite=True):
    """
    Создает копию файла с новым именем.
    @type sFileName: C{string}
    @param sFileName: Полное имя файла.
    @type sNewFileName: C{string}
    @param sNewFileName: Новое имя файла.
    @type bRewrite: C{bool}
    @param bRewrite: True-если новый файл уже существует,
        то переписать его молча. False-если новый файл уже существует,
        то не перезаписывать его а оставить старый.
    @return: Возвращает результат выполнения операции True/False.
    """
    try:
        # Проверка существования файла-источника
        if not os.path.isfile(sFileName):
            print('WARNING! File %s not exist for copy' % sFileName)
            return False

        # Проверка перезаписи уже существуещего файла
        if not bRewrite:
            print('WARNING! File %s exist and not rewrite' % sFileName)
            return False

        # Создать результирующую папку
        dir = os.path.dirname(sNewFileName)
        if not os.path.exists(dir):
            os.makedirs(dir)
        shutil.copyfile(sFileName, sNewFileName)
        return True
    except IOError:
        print('ERROR! Copy file %s I/O error' % sFileName)
        return False


def copyToDir(sFileName, sDestDir, bRewrite=True):
    """
    Копировать файл в папку.
    @type sFileName: C{string}
    @param sFileName: Имя файла.
    @type sDestDir: C{string}
    @param sDestDir: Папка в которую необходимо скопировать.
    @type bRewrite: C{bool}
    @param bRewrite: True-если новый файл уже существует,
        то переписать его молча. False-если новый файл уже существует,
        то не перезаписывать его а оставить старый.
    @return: Возвращает результат выполнения операции True/False.
    """
    return copyFile(sFileName,
                    os.path.normpath(sDestDir+'/'+os.path.basename(sFileName)), bRewrite)


def changeExt(sFileName, sNewExt):
    """
    Поменять у файла расширение.
    @type sFileName: C{string}
    @param sFileName_: Полное имя файла.
    @type sNewExt: C{string}
    @param sNewExt: Новое расширение файла (Например: '.bak').
    @return: Возвращает новое полное имя файла.
    """
    try:
        new_name = os.path.splitext(sFileName)[0]+sNewExt
        if os.path.isfile(new_name):
            os.remove(new_name)     # если файл существует, то удалить
        if os.path.exists(sFileName):
            os.rename(sFileName, new_name)
            return new_name
    except:
        print('ERROR! Cange ext file %s' % sFileName)
        raise
    return None


def fileList(sDir):
    """
    Список файлов в директории с полными путями.
    @param sDir: Исходная директория.
    @return: Список файлов.
    """
    return [norm_path(sDir+'/'+filename) for filename in os.listdir(norm_path(sDir))]


def parseCmd(sCommand):
    """
    Распарсить комманду.
    @type sCommand: c{string}
    @param sCommand: Строковое представление комманды.
    @return: Список [<Комманда>,<Аргумент1>,<Аргумент2>,..]
    """
    parse_args = sCommand.strip().split(' ')
    args = []
    i = 0
    while i < len(parse_args):
        parse_arg = parse_args[i]
        if parse_arg[0] == '"' and parse_arg[-1] != '"':
            while parse_arg[-1] != '"' and i < len(parse_args):
                i += 1
                parse_arg += ' '+parse_args[i]
        # Стереть """
        if parse_arg[0] == '"':
            parse_arg = parse_arg[1:]
        if parse_arg[-1] == '"':
            parse_arg = parse_arg[:-1]

        args.append(parse_arg)
        i += 1
    return args


def genUUID(*args):
    """
    Генерация нового UUID.
    Вид: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX.
    """
    t = long(time.time() * 1000)
    r = long(random.random()*100000000000000000L)
    a = random.random()*100000000000000000L
    data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
    data = md5.md5(data).hexdigest()
    data = data[:8]+'-'+data[8:12]+'-'+data[12:16]+'-'+data[16:20]+'-'+data[20:]
    return data


def getComputerName():
    """
    Имя компютера. Без перекодировки.
    @return: Получить имя компьютера в сети.
        Имя компьютера возвращается в utf-8 кодировке.
    """
    import socket
    comp_name = socket.gethostname()
    if isWindowsPlatform():
        # Если win то поменять кодировку c cp1251 на utf-8
        comp_name = unicode(comp_name, 'cp1251').encode('utf-8')
    return comp_name


def getComputerNameLAT():
    """
    Имя компютера. Все русские буквы заменяются латиницей.
    @return: Получить имя компьютера в сети.
    """
    comp_name = None
    if 'COMPUTERNAME' in os.environ:
        comp_name = os.environ['COMPUTERNAME']
    else:
        import socket
        comp_name = socket.gethostname()

    # ВНИМАНИЕ! Имена компьютеров должны задаваться только латиницей
    # Под Win32 можно задать имя компа русскими буквами и тогда
    # приходится заменять все на латиницу.
    if isinstance(comp_name, str):
        if isWindowsPlatform():
            comp_name = unicode(comp_name, 'cp1251')
            comp_name = rus2lat(comp_name)
    return comp_name


def _rus2lat(sText, dTranslateDict):
    """
    Перевод русских букв в латинские по словарю замен.
    @param sText: Русский текст.
    @param dTranslateDict: Словарь замен.
    """
    if not isinstance(sText, unicode):
        # Привести к юникоду
        sText = unicode(sText, 'utf-8')

    txt_list = list(sText)
    txt_list = [dTranslateDict.setdefault(ch, ch) for ch in txt_list]
    return ''.join(txt_list)


RUS2LATDict = {u'а': 'a', u'б': 'b', u'в': 'v', u'г': 'g', u'д': 'd', u'е': 'e', u'ё': 'yo', u'ж': 'j',
               u'з': 'z', u'и': 'i', u'й': 'y', u'к': 'k', u'л': 'l', u'м': 'm', u'н': 'n', u'о': 'o', u'п': 'p',
               u'р': 'r', u'с': 's', u'т': 't', u'у': 'u', u'ф': 'f', u'х': 'h', u'ц': 'c', u'ч': 'ch',
               u'ш': 'sh', u'щ': 'sch', u'ь': '', u'ы': 'y', u'ъ': '', u'э': 'e', u'ю': 'yu', u'я': 'ya',
               u'А': 'A', u'Б': 'B', u'В': 'V', u'Г': 'G', u'Д': 'D', u'Е': 'E', u'Ё': 'YO', u'Ж': 'J',
               u'З': 'Z', u'И': 'I', u'Й': 'Y', u'К': 'K', u'Л': 'L', u'М': 'M', u'Н': 'N', u'О': 'O', u'П': 'P',
               u'Р': 'R', u'С': 'S', u'Т': 'T', u'У': 'U', u'Ф': 'F', u'Х': 'H', u'Ц': 'C', u'Ч': 'CH',
               u'Ш': 'SH', u'Щ': 'SCH', u'Ь': '', u'Ы': 'Y', u'Ъ': '', u'Э': 'E', u'Ю': 'YU', u'Я': 'YA'}


def rus2lat(sText):
    """
    Перевод русских букв в латинские.
    """
    return _rus2lat(sText, RUS2LATDict)


def clear_log(sLogFileName=None, dtCurDate=None, iActualDays=None, sDateFmt='%Y-%m-%d'):
    """
    Очистить лог от неактуальных записей.
    @type sLogFileName: C{string}
    @param sLogFileName: Имя файла лога.
    @type dtCurDate: C{datetime}
    @param dtCurDate: Текущая дата отсчета.
        Если None, то берется сегодняшняя дата.
    @type iActualDays: C{integer}
    @param iActualDays: Количество актуальных дней.
    """
    if not iActualDays:
        iActualDays = get_var('LOG_ACTUAL_DAYS')
    if not iActualDays:
        # Не надо удалять записи
        return
    if not sLogFileName:
        sLogFileName = getLogFileName()
    if not os.path.exists(sLogFileName):
        # Если нет лога, то и не надо его чистить
        return

    if not dtCurDate:
        dtCurDate = datetime.datetime(1, 1, 1).today()
    actual_days = datetime.timedelta(days=iActualDays)
    actual_date = dtCurDate-actual_days
    actual_date_str = actual_date.strftime(sDateFmt)

    f = None
    try:
        f = open(sLogFileName, 'r')
        lines = f.readlines()
        f.close()
        f = None

        f = open(sLogFileName, 'w')
        for line in lines:
            date_str = line.split(' ')[0]
            if date_str > actual_date_str:
                f.write(line)
        f.close()
        f = None
    except:
        if f:
            f.close()
            f = None
        raise


def norm_path(sPath, sDelim='/'):
    """
    Удалить двойные разделител из пути.
    @type sPath: C{string}
    @param sPath: Путь
    @type sDelim: C{string}
    @param sDelim: Разделитель пути
    """
    sPath = sPath.replace('~', getHomeDir())
    dbl_delim = sDelim+sDelim
    while dbl_delim in sPath:
        sPath = sPath.replace(dbl_delim, sDelim)
    return sPath


if __name__ == '__main__':
    print(norm_path('/dsd////asdasdf///asasd///////asd'))
