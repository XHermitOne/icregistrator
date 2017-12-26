#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
Абстрактный объект системы.
Реализует общие функции для всех объектов.
"""

from ic.utils import execfunc
from ic.utils import txtgen
from ic.utils import strfunc

from . import config
from ic.utils import log

__version__ = (0, 0, 5, 2)


class icObjectProto(object):
    """
    Абстрактный объект системы.
    Абстрактный объект может обладать как качествами источника так и получателя данных.
    Поэтому в нем присутствуют как методы чтения так и записи данных.
    """
    def __init__(self, parent, *args, **kwargs):
        """
        Конструктор.
        @param parent: Объект родительского управляющего объекта.
        """
        # Объект родительского управляющего объекта
        self.parent = parent

        # Наменование объекта
        self.name = kwargs.get('name', u'Unknown')

        # Описание объекта
        self.description = kwargs.get('description', u'')

        # Имена записываемых значений в приемник данных
        self.values = kwargs.get('values', list())
        # Определяем сами переменные как ...
        for name in self.values:
            value = kwargs.get(name, None)
            setattr(self, name, value)

        # Комманды пред... и пост... обработки
        self.prev_cmd = kwargs.get('prev_cmd', None)
        self.post_cmd = kwargs.get('post_cmd', None)

    def read(self, *values):
        """
        Чтение данных из источника данных.
        @param values: Список читаемых переменных.
        @return: Список прочианных значений.
            Если переменная не найдена или произошла ошибка чтения, то
            вместо значения подставляется None с указанием WARNING в журнале сообщений.
        """
        log.warning(u'Функция чтения данных из источника данных. не определена для класса <%s>' % self.__class__.__name__)

    def read_as_dict(self, *values):
        """
        Чтение данных из источника данных.
        @param values: Список читаемых переменных.
        @return: Словарь прочианных значений.
            Если переменная не найдена или произошла ошибка чтения, то
            вместо значения подставляется None с указанием WARNING в журнале сообщений.
        """
        log.warning(u'Функция чтения данных из источника данных. не определена для класса <%s>' % self.__class__.__name__)

    def write(self, *values):
        """
        Записать данные в приемник данных.
        @param values: Список записываемых значений
        @return: True/False.
        """
        log.warning(u'Функция записи значений в приемник данных. не определена для класса <%s>' % self.__class__.__name__)

    def write_as_dict(self, **values):
        """
        Записать данные в виде словаря в приемник данных.
        @param values: Словарь записываемых значений.
        @return: True/False.
        """
        log.warning(u'Функция записи значений в приемник данных. не определена для класса <%s>' % self.__class__.__name__)

    def diagnostic(self):
        """
        Простая процедура прверки доступа к источнику данных.
        @return: True/False.
        """
        log.warning(u'Процедура диагностирования не определена для класса <%s>' % self.__class__.__name__)

    def get_context(self, state=None):
        """
        Определение контекста выполнения.
        @param state: Словарь состояния.
        @return: Словарь контекста выполнения.
        """
        context = dict()
        if state is None:
            state = dict()
        context.update(state)
        # Берем из глобального конфига
        context.update(dict([(name, config.get_cfg_var(name)) for name in config.__dict__.keys()]))
        return context

    def gen_correct_value(self, value, cur_state=None):
        """
        Генерация значения с учетом порядка блоков кодов и ссылок.
        @param value: Генерируемое значение.
        @param cur_state: Текущее состояние объекта.
        @return: Признак произведенной замены, Сгенерированное значение.
        """
        if cur_state is None:
            cur_state = dict([(name, getattr(self, name)) for name in self.values])

        if txtgen.is_genered(value):
            replace_names = txtgen.get_raplace_names(value)
            replaces = dict()
            for name in replace_names:
                if name not in cur_state:
                    log.error(u'Переменная <%s> не определена в описании объекта <%s>' % (name, self.name))
                    continue
                is_fill, replaces[name] = self.gen_correct_value(cur_state[name], cur_state)
                log.debug(u'\tЗамена <%s> => <%s> => <%s>' % (name, cur_state[name], replaces[name]))
            value = txtgen.gen(value, replaces)
            if self.parent.is_link(value):
                # Это просто ссылка без требования генерации
                value = self.parent.get_value_by_link(value)
            elif execfunc.is_code_python(value) or execfunc.is_code_func(value):
                # Это просто блок кода без требования генерации
                value = execfunc.exec_code_block(value)
            return True, value
        elif self.parent.is_link(value) and not txtgen.is_genered(value):
            # Это просто ссылка без требования генерации
            return True, self.parent.get_value_by_link(value)
        elif (execfunc.is_code_python(value) or execfunc.is_code_func(value)) and not txtgen.is_genered(value):
            # Это просто блок кода без требования генерации
            return True, execfunc.exec_code_block(value)

        return False, value

    def fill_state(self, cur_state=None):
        """
        Функция полного заполнения сстояния объекта.
        @param cur_state: Текущее заполняемое состояние объекта.
            Если не определено, то текущее состояние заполняется по всем переменным.
        @return: Заполненный словарь состояний.
        """
        if cur_state is None:
            cur_state = dict([(name, getattr(self, name)) for name in self.values])

        is_fill = False
        for name, value in cur_state.items():
            is_fill, value = self.gen_correct_value(value, cur_state)
            cur_state[name] = value
        if is_fill:
            # Продолжить генерацию значений
            return self.fill_state(cur_state)
        return cur_state

    def gen_code(self, code, context=None):
        """
        Дополнение кода информацией из контекста описания объекта.
        @param code: Строка блока кода.
        @param context: Словарь контекста, в котором генерируется код.
            Если не определен, то контекст автоматически заполняется словарем состояний.
        @return: Полностью заполненная и готовая к выполнению строка блока кода.
        """
        if not code:
            return None

        if self.cache_state is None:
            self.cache_state = self.fill_state()
        if context is None:
            context = self.get_context(self.cache_state)

        is_fill, result = self.gen_correct_value(code, context)

        return result

    def get_values_as_dict(self, values=None):
        """
        Получить внутренние переменные в виде словаря.
        @param values: Список требуемых переменных, если не определен, то берутся все переменные.
        @return: Словарь значений внутренних переменных, описанных в получателе данных.
        """
        if not values:
            values = self.values
        result = dict([(name, getattr(self, name)) for name in values])

        # Кроме того что значения были прочитаны необходимо произвести их выполнение
        for name, value in result.items():
            # INI файл д.б. в кодировке UTF-8---+
            #                                   V
            value = strfunc.toUnicode(value, 'utf-8') if not isinstance(value, unicode) else value

            result[name] = self.gen_code(value)
        return result

    def print_context(self, context):
        """
        Вывести в консоль внутренне состояние объекта источника данных.
        Функция сделана для отладки.
        """
        log.debug(u'Состояние контекста <%s>.<%s>' % (self.__class__.__name__, self.name))
        log.debug(u'\t[Переменная]\t\t[Значение]')
        for name, val in context.items():
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
