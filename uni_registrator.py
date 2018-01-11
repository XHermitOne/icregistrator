#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
icRegistrator - Программа автоматической регистрации данных из разных источников.

Параметры коммандной строки:

    python uni_registrator.py <Параметры запуска>

Параметры запуска:

    [Помощь и отладка]
        --help|-h|-?        Напечатать строки помощи
        --version|-v        Напечатать версию программы
        --debug|-d          Режим отладки
        --log|-l            Режим журналирования

    [Контроль запуска]
        --alone             Проверка монопольного выполнения (только одного экземпляра программы)

    [Дополнительные параметры]
        --run_mode=         Режимы запуска регистратора single/loop/diagnostic
        --settings=         Файл настроек. Если не определен, то берется settings.ini
"""

import sys
import commands
import getopt

from ic import config
from ic.utils import log
from ic import engine

__version__ = (0, 0, 5, 3)

# Команда проверки монопольного выполнения
PROCESS_LIST_COMMAND = 'ps -eo pid,cmd'
ALONE_CHECK_COMMAND = 'uni_registrator.py'


def main(argv):
    """
    Основная запускающая функция.
    @param argv: Список параметров коммандной строки.
    """
    # Инициализация журналирования
    log.init(config)

    # Разбираем аргументы командной строки
    try:
        options, args = getopt.getopt(argv, 'h?vdl',
                                      ['help', 'version', 'debug', 'log',
                                       'alone',
                                       'run_mode=', 'settings='])
    except getopt.error, msg:
        print(msg)
        print(u'For help use --help option')
        sys.exit(2)

    registrator = engine.icRegistrator()

    for option, arg in options:
        if option in ('-h', '--help', '-?'):
            print(__doc__)
            sys.exit(0)
        elif option in ('-v', '--version'):
            print(u'icRegister version: %s' % '.'.join([str(v) for v in __version__]))
            sys.exit(0)
        elif option in ('-d', '--debug'):
            # Установка режима отладки
            config.set_cfg_var('DEBUG_MODE', True)
        elif option in ('-l', '--log'):
            # Установка режима журналирования
            config.set_cfg_var('LOG_MODE', True)
        elif option in ('--alone',):
            processes_txt = commands.getoutput(PROCESS_LIST_COMMAND)
            processes = processes_txt.strip().split('\n')
            find_processes = [process for process in processes if ALONE_CHECK_COMMAND in process]
            if len(find_processes) > 1:
                print(u'Monopoly execute mode not imposible')
                print(u'Fileloader processes:')
                for process in find_processes:
                    print(process)
                print(u'Exit')
                return
            else:
                print(u'Monopoly execute mode ON')
        elif option in ('--run_mode',):
            # Режим запуска
            config.set_cfg_var('RUN_MODE', arg.lower())
        elif option in ('--settings',):
            # Режим запуска
            config.set_cfg_var('SETTINGS_FILENAME', arg)

    registrator.run()


if __name__ == '__main__':
    main(sys.argv[1:])
