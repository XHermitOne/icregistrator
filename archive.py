#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import os.path
import shutil
import time

import version

__version__ = (0, 0, 1, 1)

PRJ_NAME = 'icregistrator'

COPY_PATH = '/media/Transcend/'

# Не архивируемые файлы
_not_archived_file_ext = ['.dia~', '.pyc', '.PYC', '.bak', '.BAK', '.lck', '.LCK', '.log', '.LOG', '.Log',
                          '.~py', '.~PY', '.dbg', '.DBG',
                          '_pkl.frm', '_pkl.tab', '_pkl.src', '_pkl.mnu', '_pkl.acc',
                          '_pkl.mtd', '_pkl.win', '_pkl.rol', '_pkl.odb', '.edbkup']


def _del_not_archived_walk(args,cur_dir, cur_names):
    """
    Фнукция удаления ненужных файлов.
    """
    for cur_name in cur_names:
        _find_ = False
        for ext in args:
            if cur_name[-len(ext):] in args:
                _find_ = True
                break
        if _find_:
            full_name = cur_dir+'/'+cur_name
            if os.path.isfile(full_name):
                print('DELETE:', full_name)
                os.remove(full_name)


def del_all_not_archived():
    return os.path.walk(os.getcwd(), _del_not_archived_walk, tuple(_not_archived_file_ext))


def is_windows():
    """
    ОС windows?
    """
    return sys.platform[:3].lower() == 'win'


def is_linux():
    """
    ОС linux?
    """
    return sys.platform[:3].lower() == 'lin'


def copy_to_tmp():
    """
    Копирование во временную папку.
    """
    tmp_dir = os.environ.get('HOME', '')
    if __file__:
        src_dir = os.path.dirname(__file__)
    else:
        src_dir = os.getcwd()
        tmp_dir = os.tempnam()
    return shutil.copytree(src_dir, tmp_dir)


def arch():    
    version.update()    # Обновить версию

    time_start = time.time()

    print('DELETE NOT ARCHIVED FILES:')
    del_all_not_archived()
    print('...OK')

    if is_linux():
        # Перед архивированием удаляем оставшиеся архивы
        DEL_CMD = 'rm -f -v %s_linux*.zip' % PRJ_NAME
        print('DELETE FILE:', DEL_CMD)
        os.system(DEL_CMD)
    
        CUR_DATE_STR = time.strftime("_%Y_%m_%d", time.localtime(time.time()))
        ARCHIVE_CMD = 'zip -r %s_linux%s.zip *' % (PRJ_NAME, CUR_DATE_STR)
        print('RUN COMMAND:', ARCHIVE_CMD)
        os.system(ARCHIVE_CMD)
        print('...OK')

        if os.path.exists(COPY_PATH):
            DEL_CMD = 'rm -f -v %s%s_linux*.zip' % (COPY_PATH, PRJ_NAME)
            print('DELETE FILE:', DEL_CMD)
            os.system(DEL_CMD)

        MOVE_CMD = 'mv %s%s.zip %s' % (PRJ_NAME, CUR_DATE_STR, COPY_PATH)
        print('MOVE:', MOVE_CMD)
        os.system(MOVE_CMD)

    elif is_windows():
        CUR_DATE_STR = time.strftime("_%Y_%m_%d", time.localtime(time.time()))
        ARCHIVATOR = '"C:\\Program Files\\WinRAR\\WinRar.exe"'
        SWITCHES = '-r -s'
        if not os.path.exists(ARCHIVATOR):
            ARCHIVATOR = '"C:\\Program Files\\7-Zip\\7z.exe"'
            SWITCHES = '-r -tzip'
        ARCHIVE_CMD = '%s a %s %s_win32%s.zip *' % (ARCHIVATOR, SWITCHES, PRJ_NAME, CUR_DATE_STR)
        print('RUN COMMAND:', ARCHIVE_CMD)
        os.system(ARCHIVE_CMD)
        print('...OK')

    stop_time = time.time()-time_start
    print('Time:', stop_time, ' sec.', stop_time/60, 'min.')

    import imp
    ver = imp.reload(version)

    ver.printVersion()


if __name__ == '__main__':
    arch()
