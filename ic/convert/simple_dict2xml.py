#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль конвертирования словарно-списковой структуры в xml файл.
Самый простой вариант реализации.
"""

import sys
import re
from xml.sax import saxutils

from ic.utils import log

__version__ = (0, 0, 0, 2)

DEFUALT_ENCODING = 'utf-8'


class icSimpleDict2XmlWriter(saxutils.XMLGenerator):
    """
    Конвертер из словаря в XML представление.
    """

    def __init__(self, data, out=None, encoding=DEFUALT_ENCODING):
        """
        Конструктор.
        """
        self._data = data

        saxutils.XMLGenerator.__init__(self, out, encoding)

        # Отступ, определяющий вложение тегов
        self.break_line = ''

        self.time_start = 0

    def _my_write(self, text):

        if not isinstance(text, unicode):
            # ВНИМАНИЕ! Записываться в файл должен только unicode иначе падает
            # при сохранении русских букв
            text = unicode(str(text), 'utf-8')

        try:
            self._out.write(text)
        except AttributeError:
            self._write(text)

    def _startElement(self, name, attrs, auto_close=False):
        self._my_write('<' + name)
        for (name, value) in attrs.items():
            # ВНИМАНИЕ! Записываться в файл должен только unicode иначе падает
            # при сохранении русских букв
            if sys.platform[:3].lower() == 'win':
                if isinstance(value, unicode):
                    value = value.encode(self._encoding)
                txt = ' %s=%s' % (name, saxutils.quoteattr(value))
            else:
                txt = u' %s=%s' % (name, saxutils.quoteattr(value))
            if isinstance(txt, unicode):
                txt = txt.encode(self._encoding)
                self._my_write(txt)

        if auto_close:
            self._my_write('/')
        self._my_write('>')

    def _endElement(self, name, auto_close=False):
        if not auto_close:
            self._my_write('</%s>' % name)

    def startElementLevel(self, name, attrs=dict(), auto_close=False):
        """
        Начало тега.
        @name: Имя тега.
        @attrs: Атрибуты тега (словарь).
        """
        # Дописать новый отступ
        self._my_write('\n' + self.break_line)

        for item in attrs.items():
            if not isinstance(item[1], unicode):
                attrs[item[0]] = unicode(str(item[1]), self._encoding)
        self._startElement(name, attrs, auto_close)
        self.break_line += '  '

    def endElementLevel(self, name, auto_close=False):
        """
        Конец тега.
        @name: Имя, закрываемого тега.
        """
        if self.break_line:
            self.break_line = self.break_line[:-2]

        # Дописать новый отступ
        self._my_write('\n' + self.break_line)

        self._endElement(name, auto_close)

    def startElement(self, name, attrs=dict(), auto_close=False):
        """
        Начало тега.
        @name: Имя тега.
        @attrs: Атрибуты тега (словарь).
        """
        # Дописать новый отступ
        self._my_write('\n' + self.break_line)

        for item in attrs.items():
            if not isinstance(item[1], unicode):
                attrs[item[0]] = unicode(str(item[1]), self._encoding)
        self._startElement(name, attrs, auto_close)

    def endElement(self, name, auto_close=False):
        """
        Конец тега.
        @name: Имя, закрываемого тега.
        """
        self._endElement(name, auto_close)

    def parse_key(self, key_txt):
        """
        Распарсить ключ элемента.
        @param key_txt: Ключ элемента.
        @return: Имя тега, его атрибуты.
        """
        key_line = re.split(' |\n', key_txt)
        name = key_line[0]
        try:
            attrs = dict([tuple([re.sub(r'^"|"$', '', s) for s in attr_txt.split('=')]) for attr_txt in key_line[1:] if attr_txt.strip()])
        except:
            log.fatal(u'Ошибка определения атрибутов XML тега <%s>' % name)
            attrs = dict()
        return name, attrs

    def _do_write(self, data, parent_tag=None, tag_filter=None):
        """
        Процедура записи.
        @param data: Данные для записи.
        @param parent_tag: Родительский тег для
            обработки списков.
        @param tag_filter: Словарь фильтра тегов,
            определяющий список и порядок дочерних тегов для
            каждого тега.
            Порядок тегов важен для XML, поэтому введен этот фильтр.
        """
        if isinstance(data, dict):
            keys = data.keys()
            if parent_tag and tag_filter:
                keys = tag_filter.get(parent_tag, keys)

            for key in keys:
                if key not in data:
                    # Если нет таких данных,
                    # то и не вносить их в XML
                    continue
                value = data[key]
                name, attrs = self.parse_key(key)
                if not data[key] or type(data[key]) not in (dict, list):
                    self.startElement(name, attrs)
                    self._do_write(value, name, tag_filter=tag_filter)
                    self.endElement(name)
                else:
                    self.startElementLevel(name, attrs)
                    self._do_write(value, name, tag_filter=tag_filter)
                    self.endElementLevel(name)
        elif isinstance(data, list):
            for item in data:
                self._do_write(item, parent_tag, tag_filter=tag_filter)
        else:
            self._my_write(data)

    def startWrite(self, data=None, tag_filter=None):
        """
        Начало записи.
        @param data: Данные для записи.
        @param tag_filter: Словарь фильтра тегов,
            определяющий список и порядок дочерних тегов для
            каждого тега.
            Порядок тегов важен для XML, поэтому введен этот фильтр.
        """
        if data is None:
            data = self._data

        self._do_write(data, tag_filter=tag_filter)


def test():
    """
    Функция тестирования.
    """
    data = {'''ns:Documents Version="1.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:ns="http://fsrar.ru/WEGAIS/WB_DOC_SINGLE_01"
xmlns:c="http://fsrar.ru/WEGAIS/Common"
xmlns:oref="http://fsrar.ru/WEGAIS/ClientRef"
xmlns:pref="http://fsrar.ru/WEGAIS/ProductRef"
xmlns:wb="http://fsrar.ru/WEGAIS/TTNSingle"
''': {'Document': [{'Item': 'XXX'}, {'Item': '111'}, {'Item': '222'},]},
            }

    xml_file = None
    try:
        # Начать запись
        xml_file = open('/home/xhermit/.defis/text.xml', 'wt')
        xml_writer = icSimpleDict2XmlWriter(data, xml_file, encoding='utf-8')
        xml_writer.startDocument()
        xml_writer.startWrite()

        # Закончить запись
        xml_writer.endDocument()
        xml_file.close()
    except:
        if xml_file:
            xml_file.close()
        raise


if __name__ == '__main__':
    test()
