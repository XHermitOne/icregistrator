#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
Скрипт автоматической отправки XML файлов из папки за указаный диапазон времени.
"""

import os
import os.path
import datetime

XML_FILENAME_FMT = '%Y%m%d_'


def get_xml_filenames(xml_dir, start_dt, stop_dt):
    """
    Получить список файлов для отправки.
    @param xml_dir: Папка с XML файлами.
    @param start_dt: Начальное время XML файла.
    @param stop_dt: Конечное время XML файла.
    @return:
    """
    pass
