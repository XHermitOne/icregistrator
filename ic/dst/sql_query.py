#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Получатель данных в виде SQL выражения.
"""

import sqlalchemy
from ic.utils import log
from ic.utils import journal
from ic.utils import execfunc
from ic.utils import txtgen

from ic import datadst_proto

__version__ = (0, 0, 2, 1)


class icSQLQueryDataDestination(datadst_proto.icDataDestinationProto):
    """
    Получатель данных в виде SQL выражения.
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        datadst_proto.icDataDestinationProto.__init__(self, *args, **kwargs)

        # Параметры подключания к БД
        # Драйвер
        self.db_driver = kwargs.get('db_driver', 'postgresql+psycopg2')
        # Хост
        self.db_host = kwargs.get('db_host', 'localhost')
        # Порт
        self.db_port = kwargs.get('db_port', 5432)
        # Имя БД
        self.db_name = kwargs.get('db_name', None)
        # Имя пользователя
        self.db_username = kwargs.get('db_username', None)
        # Пароль
        self.db_password = kwargs.get('db_password', None)

        # SQL выражение для записи данных в приемник
        self.sql = kwargs.get('sql', None)
        # Объект связи с БД
        self.connection = None

    def get_db_url(self):
        """
        Конекшн стринг подключения к БД.
        @return: Конекшн стринг подключения к БД.
        """
        return '%s://%s:%s@%s:%s/%s' % (self.db_driver, self.db_username, self.db_password,
                                        self.db_host, self.db_port, self.db_name)

    def connect(self, db_url=None):
        """
        Соединение с БД.
        @param db_url: Конекшн стринг подключения к БД.
        @return: Объект sqlalchemy движка.
        """
        if db_url is None:
            db_url = self.get_db_url()

        if self.connection:
            self.disconnect()
            self.connection = None
        try:
            # Отображение в консоли выполняемых SQL выражений---------+
            #                                                         V
            self.connection = sqlalchemy.create_engine(db_url, echo=False)
        except:
            msg = u'Ошибка соединения с БД <%s>' % db_url
            log.fatal(msg)
            journal.write_msg(msg)
            self.connection = None
        return self.connection

    def disconnect(self, connection=None):
        """
        Разорвать соединение с БД.
        @param connection: Объект связи с БД.
        @return: True/False.
        """
        if connection is None:
            connection = self.connection

        if connection:
            connection.dispose()
            if connection == self.connection:
                self.connection = None
            connection = None
            return True
        else:
            msg = u'Не определен объект связи с БД в <%s>' % self.name
            log.warning(msg)
            journal.write_msg(msg)
        return False

    def diagnostic(self):
        """
        Простая процедура проверки доступа к источнику данных.
        @return: True/False.
        """
        log.info(u'Диагностика <%s>.<%s>' % (self.__class__.__name__, self.name))

        return self.write()

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
        if not self.sql:
            msg = u'Не определено SQL выражение для записи данных в <%s>' % self.name
            log.warning(msg)
            journal.write_msg(msg)
            return False

        sql = self.gen_sql_code(self.sql)
        if sql is None:
            msg = u'Ошибка запроса SQL'
            log.warning(msg)
            journal.write_msg(msg)
            return False

        if not sql.strip():
            msg = u'Попытка выполнения пустого запроса SQL'
            log.warning(msg)
            journal.write_msg(msg)
            return False

        try:
            self.connect()
            log.info(u'Выполнение SQL: <%s>' % sql)
            self.connection.execute(sql)
            self.disconnect()
            return True
        except:
            self.disconnect()
            msg = u'Ошибка записи данных в <%s>' % self.name
            log.fatal(msg)
            journal.write_msg(msg)
        return False

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
        return self._write(*values.keys())

    def gen_sql_code(self, code):
        """
        Дополнение кода информацией из контекста описания объекта.
        ВНИМАНИЕ! Т.к. одинарные кавычки не должны присутствовать,
        то необходимо сделать дополнительную предобработку контекста.
        @param code: Строка блока кода.
        @return: Полностью заполненная и готовая к выполнению строка блока кода.
        """
        if not code:
            return None

        if self.cache_state is None:
            self.cache_state = self.fill_state()
        context = self.get_context(self.cache_state)

        # ВНИМАНИЕ! Т.к. одинарные кавычки не должны присутствовать,
        # то необходимо сделать дополнительную предобработку контекста.
        for name, value in context.items():
            # context[name] = str(value).replace('\'', '"')
            if type(value) in (str, unicode):
                try:
                    context[name] = value.replace('\'', '"')
                except UnicodeEncodeError:
                    msg = u'Ошибка замены кавычек в значении <%s>' % value
                    log.fatal(msg)
                    journal.write_msg(msg)
        result = self.gen_code(code, context)
        return result
