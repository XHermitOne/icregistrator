#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Источник данных - список файлов.
"""

import os
import os.path
import glob

from ic.utils import log
from ic.utils import journal
from ic.utils import execfunc

from ic import datasrc_proto

__version__ = (0, 0, 1, 1)


class icFileListDataSource(datasrc_proto.icDataSourceProto):
    """
    Источник данных - список файлов.
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        datasrc_proto.icDataSourceProto.__init__(self, *args, **kwargs)

        # Список файлов задается по шаблону
        self.filename_pattern = kwargs.get('filename_pattern', None)

    def diagnostic(self):
        """
        Простая процедура проверки доступа к источнику данных.
        @return: True/False.
        """
        log.info(u'Диагностика <%s>.<%s>' % (self.__class__.__name__, self.name))

        return self.read()

    def read(self, *values):
        """
        Прочитать данные из источника данных.
        Функция выполняется с пред... и пост... обработкой.
        @param values: Список получаемых значений.
        @return: Список имен файлов.
        """
        # Перед выполнение произвести замену из контекста
        return execfunc.exec_prev_post_decorate(self._read,
                                                self.gen_code(self.prev_cmd),
                                                self.gen_code(self.post_cmd),
                                                *values)

    def _read(self, *values):
        """
        Прочитать данные из источника данных.
        @param values: Список получаемых значений.
        @return: Список имен файлов.
        """
        if not self.filename_pattern:
            msg = u'Не определен шаблон поиска файлов'
            log.warning(msg)
            journal.write_msg(msg)
            return list()

        filenames = glob.glob(self.filename_pattern)

        log.info(u'Найденные файлы:')
        for filename in filenames:
            log.info(u'\t%s' % filename)

        self.state = dict([(os.path.basename(filename), os.path.abspath(filename)) for filename in filenames])
        return filenames

    def read_as_dict(self, **values):
        """
        Прочитать данные в виде словаря из источника данных.
        Функция выполняется с пред... и пост... обработкой.
        @param values: Список получаемых значений.
        @return: Словарь {Имя файла: Полный путь до файла}.
        """
        # Перед выполнение произвести замену из контекста
        return execfunc.exec_prev_post_decorate(self._read_as_dict,
                                                self.gen_code(self.prev_cmd),
                                                self.gen_code(self.post_cmd),
                                                **values)

    def _read_as_dict(self, **values):
        """
        Прочитать данные в виде словаря из источника данных.
        @param values: Список получаемых значений.
        @return: Словарь {Имя файла: Полный путь до файла}.
        """
        filenames = self._read(*values.keys())
        self.state = dict([(os.path.basename(filename), os.path.abspath(filename)) for filename in filenames])
        return self.state

    def get_filenames(self):
        """
        Получить список прочитанных имен файлов.
        @return: Список прочитанных имен файлов.
        """
        return self.state

    def get_filepath_list(self, auto_sort=True):
        """
        Получить список прочитанных имен файлов.
        @return: Список прочитанных имен файлов.
        """
        filepaths = self.state.values()
        if auto_sort:
            filepaths.sort()
        return filepaths

    def get_filename_list(self, auto_sort=True):
        """
        Получить список прочитанных имен файлов.
        @return: Список прочитанных имен файлов.
        """
        filenames = self.state.keys()
        if auto_sort:
            filenames.sort()
        return filenames
