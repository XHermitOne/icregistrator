#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Получатель данных формата простого форматированного текстового файла.
"""

from ic.utils import log
from ic.utils import journal

from ic import datadst_proto
from ic.utils import txtgen
from ic.utils import execfunc

__version__ = (0, 0, 4, 2)


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
        # Проверка заполнения всех значений
        self.all_values = kwargs.get('all_values', False)

    def valid_all_values(self, *values):
        """
        Проверка заполнения всех значений.
        Если хотя бы одно из значений None, то зполнение считается не полным.
        @param values: Список записываемых значений
        @return: True - все значения заполнены /
            False - не заполненно хотя бы одно значение поэтому текстовый файл не генрируется.
        """
        context = self.get_values_as_dict()
        return all([context.get(name, None) not in (None, 'None') for name in values])

    def write(self, *values):
        """
        Записать данные в приемник данных.
        Функция выполняется с пред... и пост... обработкой.
        @param values: Список записываемых значений
        @return: True/False.
        """
        if self.all_values:
            # Необходимо провести проверку на заполнение всех значений
            if not self.valid_all_values(*values):
                msg = u'Не полностью заполнены входные значения для генерации файла <%s>' % str(self.output_fmt)
                log.warning(msg)
                journal.write_msg(msg)
                return False

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
            msg = u'Не указан шаблон для заполнения форматированного текстового файла.'
            log.warning(msg)
            journal.write_msg(msg)
            return False

        if self.output_fmt is None:
            msg = u'Не указан выходной файл для заполнения форматированного текстового файла.'
            log.warning(msg)
            journal.write_msg(msg)
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
            msg = u'Не указан шаблон для заполнения форматированного текстового файла.'
            log.warning(msg)
            journal.write_msg(msg)
            return False

        if self.output_fmt is None:
            msg = u'Не указан выходной файл для заполнения форматированного текстового файла.'
            log.warning(msg)
            journal.write_msg(msg)
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
