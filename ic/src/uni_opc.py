#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Источник данных UniReader Gateway.
UniReader используется как шлюз для доступа к OPC серверу.
Взаимодействие с UniReader производиться с помощью XML RPC (xmlrpclib).

ВНИМАНИЕ! В переменной values в INI файле настроек задаются только адреса читаемые из OPC сервера
Другие внутренние переменные могут учавствовать в генерации адресов, но не указываются как values.
В противном случае будет exception при чтении данных из OPC сервера.
"""

from ic.utils import log
from ic.utils import journal
from ic.utils import txtgen
from ic.utils import execfunc
from ic import config

try:
    import xmlrpclib
except ImportError:
    log.fatal(u'UniReader OPC Data Source. Import error <xmlrpclib>')

from ic import datasrc_proto

__version__ = (0, 0, 0, 1)


UNI_SERVER_URL_FMT = 'http://%s:%d'

DEFAULT_PORT = 8080


class icUniReaderOPCDataSource(datasrc_proto.icDataSourceProto):
    """
    Источник данных UniReader.
    UniReader используется как шлюз для доступа к OPC серверу.
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        datasrc_proto.icDataSourceProto.__init__(self, *args, **kwargs)

        # Хост UNI сервера для возможности удаленного подключения к OPC серверу
        self.uni_host = kwargs.get('uni_host', None)
        # Порт UNI сервера для возможности удаленного подключения
        self.uni_port = kwargs.get('uni_port', None)
        # Наименование OPC сервера источника данных
        self.opc_server = kwargs.get('opc_server', None)
        # Наименование интерфейса/топика источника данных
        self.topic = kwargs.get('topic', None)
        # Список читаемых переменных из OPC сервера
        self.addresses = kwargs.get('addresses', list())
        # Определяем сами адреса как переменные ...
        for address in self.addresses:
            value = kwargs.get(address, None)
            setattr(self, address, value)

        # OPC сервера могут возвращать Unicode в не корректной кодировке.
        self.recode_txt = kwargs.get('recode', u'')
        if self.recode_txt:
            self.recode_txt = [cp.strip() for cp in self.recode_txt.split(':')]

    def create_connection(self, host=None):
        """
        Создание объекта связи с UniReader XMLRPC сервером.
        @param host: Хост OPC сервера для возможности удаленного подключения (через DCOM) к OPC серверу.
            Если не определен, то считается что OPC сервер находится локально.
        @return: Объект Uni - сервера.
        """
        if type(host) not in (None.__class__, str, unicode):
            msg = u'UniReader. Не корректный тип хоста OPC сервера <%s>' % type(host)
            log.error(msg)
            journal.write_msg(msg)
            return None

        is_local_opc = (host is None) or (type(host) in (str, unicode) and host.lower().strip() in ('localhost', '127.0.0.1'))
        if is_local_opc:
            log.info(u'UniReader. OPC сервер находится локально')
        else:
            log.info(u'UniReader. OPC сервер находится на <%s>' % host)

        url = UNI_SERVER_URL_FMT % (host, self.uni_port)
        log.info(u'UniReader. URL для подключения к Uni-серверу: <%s>' % url)
        connection = xmlrpclib.ServerProxy(url)
        return connection

    def recode(self, value, src_encoding=None, dst_encoding=None):
        """
        Произвести перекодировку Unicode строки.
        OPC сервера могут возвращать Unicode в не корректной кодировке.
        Например:
            s = u'\xcf\xe8\xe2\xee \xf1\xe2\xe5\xf2\xeb\xee\xe5 "\xc0\xe1\xe0\xea\xe0\xed\xf1\xea\xee\xe5", 4,800%, 0,500'
            чтобы получить Unicode в корректной кодировке необходимо произвести:
            s = s.encode('cp1252').decode('cp1251')
        @param value: Значение.
        @param src_encoding: Исходная кодировка. cp1252 в примере.
        @param dst_encoding: Результирующая кодировка. cp1251 в примере.
        @return: Перекодированная строка Unicode.
        """
        if (self.recode_txt is None) and (src_encoding is None) and (dst_encoding is None):
            # Перекодировать не надо
            return value
        else:
            # Необходимо произвести перекодировку только строковых значений
            if isinstance(value, unicode):
                src_encoding = (txtgen.DEFAULT_ENCODING if not self.recode_txt else self.recode_txt[0]) if not src_encoding else src_encoding
                dst_encoding = (txtgen.DEFAULT_ENCODING if not self.recode_txt else self.recode_txt[1]) if not dst_encoding else dst_encoding
                value = value.encode(src_encoding).decode(dst_encoding)
        return value

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

    def _gen_addresses(self, *addresses_values):
        """
        Подготовка адресов для чтения. Генерация адресов OPC-сервера.
        @param addresses_values: Список имен переменных читаемых адресов.
        @return: Список сгенерированных адресов.
            Адреса всегда задаются строками.
        """
        addresses = list()
        for value in addresses_values:
            code = getattr(self, value)
            address = self.gen_code(code)
            if value in self.values:
                # Если имя адреса используется в генерации других адресов,
                # то надо обновить значение для следующей генерации
                link_value = self._read_value(address)
                setattr(self, value, link_value)
                self.cache_state[value] = link_value
            addresses.append(address)
        return addresses

    def _read_value(self, address):
        """
        Прочитать значение по адресу из OPC сервера.
        @param address: Адрес. Адрес задается явно.
        @return: Прочитанное значение либо None в случае ошибки.
        """
        connection = None
        try:
            # Создание связи
            connection = self.create_connection(self.uni_host)
            if connection is None:
                msg = u'Не возможно создать объект связи с UniReader. Хост <%s>' % self.uni_host
                log.error(msg)
                journal.write_msg(msg)
                return None

            # Контроль наличия процедуры чтения значений из OPC сервера
            rpc_methods = connection.system.listMethods()
            if 'sources.ReadValueAsString' not in rpc_methods:
                msg = u'UniReader. Процедура чтения значения из OPC сервера не найдена. Хост <%s>' % self.uni_host
                log.error(msg)
                journal.write_msg(msg)
                return None

            # Прочитать из OPC сервера
            val = connection.sources.ReadValueAsString('OPC_SERVER_NODE', self.opc_server, address)
            result = self.recode(val[0]) if val else None

            log.debug(u'UniReader. Адрес <%s>. Результат чтения данных %s' % (address, result))
            return result
        except:
            msg = u'UniReader. Ошибка чтения значения по адресу <%s> в <%s>' % (address, self.__class__.__name__)
            log.fatal(msg)
            journal.write_msg(msg)
        return None

    def _read(self, *values):
        """
        Чтение данных из источника данных.
        @param values: Список читаемых переменных.
        @return: Список прочитанных значений.
            Если переменная не найдена или произошла ошибка чтения, то
            вместо значения подставляется None с указанием WARNING в журнале сообщений.
        """
        connection = None

        if not values:
            log.warning(u'UniReader. Не определены переменные для чтения в <%s>' % self.name)
            values = self.addresses
            log.debug(u'UniReader. Переменные взяты из описания источника данных: %s' % values)

        try:
            # Создание клиента OPC
            connection = self.create_connection(self.uni_host)
            if connection is None:
                msg = u'Не возможно создать объект связи с UniReader. Хост <%s>' % self.uni_host
                log.error(msg)
                journal.write_msg(msg)
                return None

            # Контроль наличия процедуры чтения значений из OPC сервера
            rpc_methods = connection.system.listMethods()
            if 'sources.ReadValueAsString' not in rpc_methods:
                msg = u'UniReader. Процедура чтения значения из OPC сервера не найдена. Хост <%s>' % self.uni_host
                log.error(msg)
                journal.write_msg(msg)
                return None

            # Подготовка переменных для чтения
            # Адреса всегда задаются строками
            addresses = self._gen_addresses(*values)
            log.debug(u'UniReader. Чтение адресов %s' % addresses)

            # Прочитать из OPC сервера
            result = list()
            for address in addresses:
                value = connection.sources.ReadValueAsString('OPC_SERVER_NODE', self.opc_server, address)
                result.append(self.recode(value) if value else None)

            # Регистрация состояния
            state = dict([(values[i], val) for i, val in enumerate(result)])
            self.reg_state(**state)

            log.debug(u'UniReader. Результат чтения данных:')
            for i, value in enumerate(result):
                log.debug(u'\t%s\t=\t%s' % (addresses[i], value))

            return result
        except:
            msg = u'UniReader. Ошибка чтения данных <%s>' % self.__class__.__name__
            log.fatal(msg)
            journal.write_msg(msg)
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
            log.warning(u'UniReader. Не определены переменные для чтения в <%s>' % self.name)
            values = self.addresses
            log.debug(u'UniReader. Переменные взяты из описания источника данных: %s' % values)

        read_list = self.read(*values)
        result = None
        if read_list is None:
            return None
        elif not read_list and isinstance(read_list, list):
            return dict()
        elif read_list and isinstance(read_list, list):
            result = dict([(values[i], val) for i, val in enumerate(read_list)])
        log.debug(u'UniReader. Результат чтения данных в виде словаря %s' % result)
        return result

    def diagnostic(self):
        """
        Простая процедура прверки доступа к источнику данных.
        @return: True/False.
        """
        connection = None

        log.info(u'UniReader. Диагностика <%s>.<%s>' % (self.__class__.__name__, self.name))

        if self.opc_server is None:
            msg = u'UniReader. Не определен OPC сервер в <%s>' % self.name
            log.warning(msg)
            journal.write_msg(msg)
            return False

        if self.topic is None:
            msg = u'UniReader. Не определен топик в <%s>' % self.name
            log.warning(msg)
            journal.write_msg(msg)
            return False

        try:
            # Создание клиента OPC
            connection = self.create_connection(self.uni_host)
            if connection is None:
                msg = u'Не возможно создать объект связи с UniReader. Хост <%s>' % self.uni_host
                log.error(msg)
                journal.write_msg(msg)
                return None

            # Контроль наличия процедуры чтения значений из OPC сервера
            rpc_methods = connection.system.listMethods()
            if 'sources.ReadValueAsString' not in rpc_methods:
                msg = u'UniReader. Процедура чтения значения из OPC сервера не найдена. Хост <%s>' % self.uni_host
                log.error(msg)
                journal.write_msg(msg)
                return None
            else:
                log.info(u'UniReader. Список методов удаленного вызова %s' % str(rpc_methods))

            return True
        except:
            msg = u'UniReader. Ошибка диагностики <%s>' % self.__class__.__name__
            log.fatal(msg)
            journal.write_msg(msg)
        return False
