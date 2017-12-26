#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Получатель данных формата простого форматированного текстового файла.
"""

from ic.utils import log

from ic import datadst_proto
from ic.utils import txtgen
from ic.utils import execfunc

__version__ = (0, 0, 2, 2)


class icTxtFmtDataDestination(datadst_proto.icDataDestinationProto):
    """
    Получатель данных формата простого форматированного текстового файла..
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        datadst_proto.icDataDestinationProto.__init__(self, *args, **kwargs)

        # Заполняемый шаблон
        self.template_fmt = kwargs.get('template', None)
        # Выходной файл
        self.output_fmt = kwargs.get('output', None)

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
        if self.template_fmt is None:
            log.warning(u'Не указан шаблон для заполнения форматированного текстового файла.')
            return False

        if self.output_fmt is None:
            log.warning(u'Не указан выходной файл для заполнения форматированного текстового файла.')
            return False

        context = self.get_values_as_dict()
        template = txtgen.gen(self.template_fmt, context)
        output = txtgen.gen(self.output_fmt, context)

        # Заполняем шаблон переменными
        gen_result = txtgen.gen_txt_file(template, output, context)
        return gen_result

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
        if self.template_fmt is None:
            log.warning(u'Не указан шаблон для заполнения форматированного текстового файла.')
            return False

        if self.output_fmt is None:
            log.warning(u'Не указан выходной файл для заполнения форматированного текстового файла.')
            return False

        context = self.get_values_as_dict()
        self.print_context(context)
        template = txtgen.gen(self.template_fmt, context)
        output = txtgen.gen(self.output_fmt, context)

        # Заполняем шаблон переменными
        gen_result = txtgen.gen_txt_file(template, output, context)
        return gen_result

    def diagnostic(self):
        """
        Простая процедура прверки доступа к источнику данных.
        @return: True/False.
        """
        log.info(u'Диагностика <%s>.<%s>' % (self.__class__.__name__, self.name))

        return self.write()
