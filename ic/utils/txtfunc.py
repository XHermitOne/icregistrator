#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Функции работы с текстовыми файлами.
"""

# --- Imports ---
import os
import os.path

from .ic_extend import save_file_text
from .ic_extend import load_file_text

# Эти функции добавлены для возможности
# импортировать их из этого модуля
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
from .ic_extend import load_file_unicode
from .ic_extend import recode_text_file
from .ic_extend import text_file_append
from .ic_extend import text_file_find
from .ic_extend import text_file_replace
from .ic_extend import text_file_subdelete
from .ic_extend import text_file_subreplace
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

from . import ic_extend
from . import ic_str
from . import log

__version__ = (0, 0, 1, 1)

DEFAULT_ENCODING = 'utf-8'


def save_file_csv(csv_filename, records=(),
                  delim=u',', encoding=DEFAULT_ENCODING):
    """
    Запись в CSV файл списка записей.
    @param csv_filename: Имя CSV файла.
    @param records: Список записей.
        Каждая запись представляет собой список значений полей.
    @param delim: Разделитель.
    @param encoding: Кодировка результирующего файла.
    @return: True/False
    """
    txt = u'\n'.join([delim.join([ic_str.toUnicode(field, encoding) for field in record]) for record in records])
    return save_file_text(csv_filename, txt)


def load_file_csv(csv_filename, delim=u',',
                  encoding=DEFAULT_ENCODING, to_unicode=True):
    """
    Чтение csv файла в виде списка записей.
    @param csv_filename; Имя CSV файла.
    @param delim: Разделитель.
    @param encoding: Кодовая страница файла
        (для преобразования в Unicode).
    @paran to_unicode: Преобразовать сразу в Unicode?
    @return: Список записей.
        Каждая запись представляет собой список значений полей.
        Либо None в слечае ошибки.
    """
    if not os.path.exists(csv_filename):
        log.warning(u'Файл <%s> не найден' % csv_filename)
        return None

    txt = load_file_text(csv_filename,
                         code_page=encoding, to_unicode=to_unicode)
    if txt:
        txt = txt.strip()

        try:
            records = list()
            txt_lines = txt.split(u'\n')
            for txt_line in txt_lines:
                record = [ic_extend.wise_type_translate_str(field) for field in txt_line.split(delim)]
                records.append(record)
            return records
        except:
            log.fatal(u'Ошибка конвертации содержимого CSV файла <%s> в список записей' % csv_filename)
    return None
