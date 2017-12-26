#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
Модуль интерфейса абстрактного получателя данных.
"""

from . import obj_proto

__version__ = (0, 0, 5, 2)


class icDataDestinationProto(obj_proto.icObjectProto):
    """
    Интерфейс абстрактного получателя данных.
    Любой класс получателя данных должен наследоваться от этого класса.
    """
    def __init__(self, parent, *args, **kwargs):
        """
        Конструктор.
        @param parent: Объект родительского управляющего объекта.
        """
        obj_proto.icObjectProto.__init__(self, parent, *args, **kwargs)

        # Кеш состояния объекта
        self.cache_state = None

    def clear_state_cache(self):
        """
        Очистить кеш состояния объекта.
        """
        self.cache_state = None
