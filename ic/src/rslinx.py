#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Источник данных OPC сервер RSLinx.
Взаимодействие с RSLinx производиться через библиотеку Python
OpenRPC (http://openopc.sourceforge.net).

ВНИМАНИЕ! В переменной values в INI файле настроек задаются только адреса читаемые из OPC сервера
Другие внутренние переменные могут учавствовать в генерации адресов, но не указываются как values.
В противном случае будет exception при чтении данных из OPC сервера.
"""

from ic.utils import log
from ic.utils import txtgen
from ic.utils import execfunc
from ic import config

try:
    import OpenOPC
except ImportError:
    log.fatal(u'RSLinx Data Source. Import error <OpenOPC>')

from ic import datasrc_proto

__version__ = (0, 0, 4, 3)


class icRSLinxDataSource(datasrc_proto.icDataSourceProto):
    """
    Источник данных OPC сервер RSLinx.
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        datasrc_proto.icDataSourceProto.__init__(self, *args, **kwargs)

        # Хост OPC сервера для возможности удаленного подключения (через DCOM) к OPC серверу
        self.opc_host = kwargs.get('opc_host', None)
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
        self.recode_txt = kwargs.get('recode', None)
        if self.recode_txt:
            self.recode_txt = [cp.strip() for cp in self.recode_txt.split(':')]

    def create_opc_client(self, opc_host=None):
        """
        Создание объекта OPC клиента.
        @param opc_host: Хост OPC сервера для возможности удаленного подключения (через DCOM) к OPC серверу.
            Если не определен, то считается что OPC сервер находится локально.
        @return: Объект OPC сервера.
        """
        if type(opc_host) not in (None.__class__, str, unicode):
            log.error(u'Не корректный тип хоста OPC сервера <%s>' % type(opc_host))
            return None

        is_local_opc = (opc_host is None) or (type(opc_host) in (str, unicode) and opc_host.lower().strip() in ('localhost', '127.0.0.1'))
        if is_local_opc:
            log.info(u'OPC сервер находится локально')
            opc = OpenOPC.client()
        else:
            log.info(u'OPC сервер находится на <%s>' % opc_host)
            opc = OpenOPC.open_client(opc_host)
        return opc

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
                src_encoding = (txtgen.DEFAULT_ENCODING if self.recode_txt is None else self.recode_txt[0]) if src_encoding is None else src_encoding
                dst_encoding = (txtgen.DEFAULT_ENCODING if self.recode_txt is None else self.recode_txt[1]) if dst_encoding is None else dst_encoding
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
        Подготовка адресов для чтения. Генерация адресов RSLinx.
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
        Прочитать значение по адресу из RSLinx.
        @param address: Адрес. Адрес задается явно.
        @return: Прочитанное значение либо None в случае ошибки.
        """
        opc = None
        try:
            # Создание клиента OPC
            opc = self.create_opc_client(self.opc_host)
            if opc is None:
                log.error(u'Не возможно создать объект клиента OPC. Хост <%s>' % self.opc_host)
                return None

            # Список серверов OPC
            servers = opc.servers()
            if self.opc_server not in servers:
                log.warning(u'Сервер <%s> не найден среди %s' % (self.opc_server, servers))
                opc.close()
                return None

            # Соедиенение с сервером
            server = self.opc_server
            opc.connect(server)

            # Прочитать из OPC сервера
            val = opc.read(address)
            result = self.recode(val[0]) if val and val[1] == 'Good' else None

            opc.close()

            log.debug(u'Адрес <%s>. Результат чтения данных %s' % (address, result))
            return result
        except:
            if opc:
                opc.close()
            log.fatal(u'Ошибка чтения значения по адресу <%s> в <%s>' % (address, self.__class__.__name__))
        return None

    def _read(self, *values):
        """
        Чтение данных из источника данных.
        @param values: Список читаемых переменных.
        @return: Список прочитанных значений.
            Если переменная не найдена или произошла ошибка чтения, то
            вместо значения подставляется None с указанием WARNING в журнале сообщений.
        """
        opc = None

        if not values:
            log.warning(u'Не определены переменные для чтения в <%s>' % self.name)
            values = self.addresses
            log.debug(u'Переменные взяты из описания источника данных: %s' % values)

        try:
            # Создание клиента OPC
            opc = self.create_opc_client(self.opc_host)
            if opc is None:
                log.error(u'Не возможно создать объект клиента OPC. Хост <%s>' % self.opc_host)
                return None

            # Список серверов OPC
            servers = opc.servers()
            if self.opc_server not in servers:
                log.warning(u'Сервер <%s> не найден среди %s' % (self.opc_server, servers))
                opc.close()
                return None

            # Соедиенение с сервером
            server = self.opc_server
            opc.connect(server)

            # Подготовка переменных для чтения
            # Адреса всегда задаются строками
            addresses = self._gen_addresses(*values)
            log.debug(u'Чтение адресов %s' % addresses)
            # Прочитать из OPC сервера
            result = [self.recode(val[1]) if val and val[2] == 'Good' else None for val in opc.read(addresses)]

            # result = [val.encode('') if isinstance(val, unicode) else val for val in result]
            # result = [val for val in opc.read(addresses)]

            opc.close()

            # Регистрация состояния
            state = dict([(values[i], val) for i, val in enumerate(result)])
            self.reg_state(**state)

            log.debug(u'Результат чтения данных %s' % result)
            return result
        except:
            if opc:
                opc.close()
            log.fatal(u'Ошибка чтения данных <%s>' % self.__class__.__name__)
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
            log.warning(u'Не определены переменные для чтения в <%s>' % self.name)
            values = self.addresses
            log.debug(u'Переменные взяты из описания источника данных: %s' % values)

        read_list = self.read(*values)
        result = None
        if read_list is None:
            return None
        elif not read_list and isinstance(read_list, list):
            return dict()
        elif read_list and isinstance(read_list, list):
            result = dict([(values[i], val) for i, val in enumerate(read_list)])
        log.debug(u'Результат чтения данных в виде словаря %s' % result)
        return result

    def diagnostic(self):
        """
        Простая процедура прверки доступа к источнику данных.
        @return: True/False.
        """
        opc = None

        log.info(u'Диагностика <%s>.<%s>' % (self.__class__.__name__, self.name))

        if self.opc_server is None:
            log.warning(u'Не определен OPC сервер в <%s>' % self.name)
            return False

        if self.topic is None:
            log.warning(u'Не определен топик в <%s>' % self.name)
            return False

        try:
            # Создание клиента OPC
            opc = self.create_opc_client(self.opc_host)
            if opc is None:
                log.error(u'Не возможно создать объект клиента OPC. Хост <%s>' % self.opc_host)
                return None

            # Список серверов OPC
            servers = opc.servers()
            if self.opc_server not in servers:
                log.warning(u'Сервер <%s> не найден среди %s' % (self.opc_server, servers))
                opc.close()
                return False

            server = self.opc_server
            log.info(u'Диагностика OPC сервера <%s>' % server)
            # Соедиенение с сервером
            opc.connect(server)

            # Вывод состояния сервера
            log.info(u'Общая информация о OPC сервере')
            info_list = opc.info()
            for inf in info_list:
                log.info(u'\t%s' % str(inf))

            # Список интерфейсов servers
            topics = opc.list()
            if self.topic not in topics:
                log.warning(u'Топик <%s> не найден среди %s' % (self.topic, topics))
                opc.close()
                return False

            # Режимы одного топика
            topic = topics[topics.index(self.topic)]
            log.info(u'Топик/Интерфейс: %s' % topic)
            modes = opc.list(topic)
            log.info(u'\tРежимы: %s' % modes)

            # Переменные
            for mode in modes:
                address = topic+u'.'+mode
                tags = opc.list(address)
                log.info(u'\t\tТеги <%s>:' % address)
                for tag in tags:
                    log.info(u'\t\t\t%s' % tag)

            # Закрытие соединения
            opc.close()
            return True
        except:
            if opc:
                opc.close()
            log.fatal(u'Ошибка диагностики <%s>' % self.__class__.__name__)
        return False
