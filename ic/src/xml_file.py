#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Источник данных абстрактного XML файла.

Переменные могут читаться из XML файла методом указания пути.
Например:
root/Documents/1/Document/Title/value
"""

import os
import os.path
import glob
from ic.utils import log
from ic.utils import journal
from ic.utils import execfunc
from ic.utils import xmlfunc

from ic import datasrc_proto

__version__ = (0, 0, 2, 1)


class icXMLFileDataSource(datasrc_proto.icDataSourceProto):
    """
    Источник данных абстрактного XML файла.
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        datasrc_proto.icDataSourceProto.__init__(self, *args, **kwargs)

        # Полное наименование XML файла - источника данных
        # Либо шаблон обрабатываемых файлов
        # Если такого файла не найдено или в имени присутствуют * или ?,
        # то считается что это шаблон файлов
        # В этом случае в качестве значений состояний будут списки значений
        self.xml_filename = kwargs.get('xml_filename', None)

        # Признак удаления файлов после обработки
        self.auto_remove = kwargs.get('auto_remove', False)

        self.cache_xml_filenames = list()

    def read(self, *values):
        """
        Чтение данных из источника данных.
        Чтение выполняется с пред... и пост... обработкой.
        @param values: Список читаемых переменных.
        @return: Список прочианных значений.
            Если переменная не найдена или произошла ошибка чтения, то
            вместо значения подставляется None с указанием WARNING в журнале сообщений.
        """
        # Перед выполнение произвести замену из контекста
        return execfunc.exec_prev_post_decorate(self._read,
                                                self.gen_code(self.prev_cmd),
                                                self.gen_code(self.post_cmd),
                                                *values)

    def _read(self, *values):
        """
        Чтение данных из источника данных.
        @param values: Список читаемых переменных.
        @return: Список прочианных значений.
            Если переменная не найдена или произошла ошибка чтения, то
            вместо значения подставляется None с указанием WARNING в журнале сообщений.
        """
        xml_filenames = self.get_xml_filenames()

        if not values:
            log.warning(u'Не определены переменные для чтения в <%s>' % self.name)
            values = self.values
            log.debug(u'Переменные взяты из описания источника данных: %s' % values)

        try:
            result = [list() for i in range(len(values))]
            for xml_filename in xml_filenames:
                # Получаем содержимое XML файла
                xml_content = xmlfunc.load_xml_content(xml_filename)
                for i, value in enumerate(values):
                    value_path = getattr(self, value)
                    xml_value = xmlfunc.get_xml_content_by_link(xml_content, value_path)
                    result[i].append(xml_value)

            # Регистрация состояния
            state = dict([(values[i], val) for i, val in enumerate(result)])
            self.reg_state(**state)

            if self.auto_remove:
                for xml_filename in xml_filenames:
                    if os.path.exists(xml_filename):
                        try:
                            log.info(u'Удаление файла <%s>' % xml_filename)
                            os.remove(xml_filename)
                        except:
                            msg = u'Ошибка удаления файла <%s>' % xml_filename
                            log.fatal(msg)
                            journal.write_msg(msg)

            return result
        except:
            log.fatal(u'Ошибка чтения данных из файлов %s' % xml_filenames)

        return None

    def read_as_dict(self, *values):
        """
        Чтение данных из источника данных.
        @param values: Список читаемых переменных.
        @return: Словарь прочианных значений.
            Если переменная не найдена или произошла ошибка чтения, то
            вместо значения подставляется None с указанием WARNING в журнале сообщений.
        """
        if not values:
            log.warning(u'Не определены переменные для чтения в <%s>' % self.name)
            values = self.values
            log.debug(u'Переменные взяты из описания источника данных: %s' % values)

        read_list = self.read(*values)
        result = None
        if read_list is None:
            return None
        elif not read_list and isinstance(read_list, list):
            return dict()
        elif read_list and isinstance(read_list, list):
            result = dict([(values[i], val) for i, val in enumerate(read_list)])
        log.debug(u'Результат чтения данных в виде словаря %s' % result)
        return result

    def is_filename_pattern(self, filename):
        """
        Проверка является имя файла шаблоном.
        @param filename: Имя файла.
        @return: True/False.
        """
        if not filename:
            return False
        return '*' in filename or '?' in filename

    def get_xml_filenames(self):
        """
        Определить список обрабатываемых XML файлов.
        @return: Cписок обрабатываемых XML файлов.
        """
        if self.cache_xml_filenames:
            # Работаем с мгновенным слепком списка файлов
            return self.cache_xml_filenames

        if self.xml_filename is None:
            msg = u'Не определены XML файлы источника данных <%s>' % self.__class__.__name__
            log.warning(msg)
            journal.write_msg(msg)
            return list()

        xml_filenames = list()
        if self.is_filename_pattern(self.xml_filename):
            # Если это шаблон, то получить список файлов
            xml_filenames = glob.glob(self.xml_filename)

            log.info(u'Найдены XML файлы в <%s>:' % self.xml_filename)
            for xml_filename in xml_filenames:
                log.info(u'\t%s' % xml_filename)

        # Это указание конкретного файла
        if os.path.exists(self.xml_filename):
            self.cache_xml_filenames = [self.xml_filename]
            return self.cache_xml_filenames
        # else:
        #     log.warning(u'Не найден XML файл <%s> источника данных' % self.xml_filename)
        self.cache_xml_filenames = xml_filenames
        return self.cache_xml_filenames

    def diagnostic(self):
        """
        Простая процедура прверки доступа к источнику данных.
        @return: True/False.
        """
        result = False
        xml_filenames = self.get_xml_filenames()
        if xml_filenames:
            xml_file_exists = [os.path.exists(xml_filename) for xml_filename in xml_filenames]
            result = sum(xml_file_exists) == len(xml_file_exists)

        # Прочитать данные
        read_data = self.read_as_dict()
        log.debug(u'Прочитанные данные:')
        for name, value in read_data.items():
            log.debug(u'\t<%s>\t%s' % (name, value))

        return result
