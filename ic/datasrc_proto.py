#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
Модуль интерфейса абстрактного источника данных.
"""

from ic.utils import log
from ic.utils import txtgen
from ic.utils import strfunc

from . import obj_proto

__version__ = (0, 0, 5, 3)


class icDataSourceProto(obj_proto.icObjectProto):
    """
    Интерфейс абстрактного источника данных.
    Любой класс источника данных должен наследоваться от этого класса.
    """
    def __init__(self, parent, *args, **kwargs):
        """
        Конструктор.
        @param parent: Объект родительского управляющего объекта.
        """
        obj_proto.icObjectProto.__init__(self, parent, *args, **kwargs)

        # ВНИМАНИЕ! Источники данных запоминают после чтения состояние переменных для
        # последующего доступа к ним объектов приемников данных
        # Вот это словарь переменных
        self.state = dict()
        # Тоже самое для кеширования (кеш сбрасывается в конце каждого такта обработки)
        self.cache_state = None

    def reg_state(self, **values):
        """
        Зарегистрировать значения переменных в словаре внутренного состояния.
        @param values: Словарь переменных.
        """
        self.state.update(values)

    def print_state(self):
        """
        Вывести в консоль внутренне состояние объекта источника данных.
        Функция сделана для отладки.
        """
        log.debug(u'Состояние источника данных <%s>.<%s>' % (self.__class__.__name__, self.name))
        log.debug(u'\t[Переменная]\t\t[Значение]')
        for name, val in self.state.items():
            try:
                val_codepage = strfunc.get_codepage(val) if isinstance(val, str) else txtgen.DEFAULT_ENCODING
                if val_codepage is None:
                    val_codepage = txtgen.DEFAULT_ENCODING

                val = unicode(str(val), val_codepage) if not isinstance(val, unicode) else val
                log.debug(u'\t<%s>\t\t<%s>' % (name, val))
            except UnicodeDecodeError:
                log.error(u'Ошибка отображения состояния переменной <%s>' % name)
            except UnicodeEncodeError:
                log.error(u'Ошибка отображения состояния переменной <%s>' % name)

    def clear_state_cache(self):
        """
        Очистить кеш состояния объекта.
        """
        self.cache_state = None
