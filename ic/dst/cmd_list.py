#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Получатель данных из источников и преобразователь из в виде списка комманд.
"""

from ic.utils import log

from ic import datadst_proto
from ic.utils import execfunc

__version__ = (0, 0, 0, 1)


class icCmdListDataDestination(datadst_proto.icDataDestinationProto):
    """
    Получатель данных из источников и преобразователь из в виде списка комманд.
    Каждое значение воспринимается как отдельная комманда.
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        datadst_proto.icDataDestinationProto.__init__(self, *args, **kwargs)

    def write(self, *values):
        """
        Записать данные в приемник данных.
        Функция выполняется с пред... и пост... обработкой.
        @param values: Список записываемых значений
        @return: True/False.
        """
        # Перед выполнение произвести замену из контекста
        return execfunc.exec_prev_post_decorate(self._write,
                                                self.gen_code(self.prev_cmd),
                                                self.gen_code(self.post_cmd),
                                                *values)

    def _write(self, *values):
        """
        Записать данные в приемник данных.
        @param values: Список записываемых значений
        @return: True/False.
        """
        if not values:
            log.warning(u'Не определены переменные для записи')
            values = self.values
            log.debug(u'Взяты переменные из описания объекта: %s' % values)

        context = self.get_values_as_dict()
        self.print_context(context)

        result = True
        for value in values:
            cmd = self.gen_code(value, context)
            # execfunc.exec_code_block(cmd)
        return result

    def write_as_dict(self, **values):
        """
        Записать данные в виде словаря в приемник данных.
        Функция выполняется с пред... и пост... обработкой.
        @param values: Словарь записываемых значений.
        @return: True/False.
        """
        # Перед выполнение произвести замену из контекста
        return execfunc.exec_prev_post_decorate(self._write_as_dict,
                                                self.gen_code(self.prev_cmd),
                                                self.gen_code(self.post_cmd),
                                                **values)

    def _write_as_dict(self, **values):
        """
        Записать данные в виде словаря в приемник данных.
        @param values: Словарь записываемых значений.
        @return: True/False.
        """
        if not values:
            log.warning(u'Не определены переменные для записи')
            values = self.get_values_as_dict()
            log.debug(u'Взяты переменные из описания объекта: %s' % values)

        context = self.get_values_as_dict()
        self.print_context(context)

        result = True
        for value in values.values():
            cmd = self.gen_code(value, context)
            # execfunc.exec_code_block(cmd)
        return result

    def diagnostic(self):
        """
        Простая процедура прверки доступа к источнику данных.
        @return: True/False.
        """
        log.info(u'Диагностика <%s>.<%s>' % (self.__class__.__name__, self.name))

        return self.write()
