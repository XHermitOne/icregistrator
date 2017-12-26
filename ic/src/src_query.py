#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Источник данных - результат выполнения SQL выражения.
Обычно в качестве SQL выражения выступает SELECT.
"""

import sqlalchemy
from ic.utils import log
from ic.utils import execfunc

from ic import datasrc_proto

__version__ = (0, 0, 0, 1)


class icSQLQueryDataSource(datasrc_proto.icDataSourceProto):
    """
    Источник данных - результат выполнения SQL выражения.
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        datasrc_proto.icDataSourceProto.__init__(self, *args, **kwargs)
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

        # Результат выполнения SQL выражения/Рекордсет
        # Рекордсет фиксируется в словаре состояния объекта
        self.recordset = list()

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
            log.fatal(u'Ошибка соединения с БД <%s>' % db_url)
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
            log.warning(u'Не определен объект связи с БД в <%s>' % self.name)
        return False

    def diagnostic(self):
        """
        Простая процедура проверки доступа к источнику данных.
        @return: True/False.
        """
        log.info(u'Диагностика <%s>.<%s>' % (self.__class__.__name__, self.name))

        return self.read()

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
            context[name] = str(value).replace('\'', '"')

        result = self.gen_code(code, context)
        return result

    def read(self, *values):
        """
        Прочитать данные из источника данных.
        Функция выполняется с пред... и пост... обработкой.
        @param values: Список получаемых значений.
        @return: Список записей/рекордсет.
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
        @return: Список записей/рекордсет.
        """
        self.recordset = list()
        if not self.sql:
            log.warning(u'Не определено SQL выражение для получения данных в <%s>' % self.name)
            self.reg_state(recordset=self.recordset)
            return self.recordset

        sql = self.gen_sql_code(self.sql)
        if not sql.strip():
            log.warning(u'Попытка выполнения пустого запроса SQL')
            self.reg_state(recordset=self.recordset)
            return self.recordset

        try:
            self.connect()
            log.info(u'Выполнение SQL: <%s>' % sql)
            recordset = self.connection.execute(sql)
            self.disconnect()
            self.recordset = [dict(rec) for rec in recordset]
            log.debug(u'Результат запроса: %s' % str(self.recordset))
        except:
            self.disconnect()
            log.fatal(u'Ошибка получения данных в <%s>' % self.name)
            self.recordset = list()
        self.reg_state(recordset=self.recordset)
        return self.recordset

    def read_as_dict(self, **values):
        """
        Прочитать данные в виде словаря из источника данных.
        Функция выполняется с пред... и пост... обработкой.
        @param values: Список получаемых значений.
        @return: Список записей/рекордсет.
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
        @return: Список записей/рекордсет.
        """
        return self._read(*values.keys())
