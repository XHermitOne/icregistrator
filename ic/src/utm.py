#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Источник данных УТМ.

Этот класс используется для чтения XML из УТМ и последующего извлечения данных.
"""

import os
import os.path
import uuid
import datetime
import shutil

from ic.utils import log
from ic.utils import execfunc
from ic.utils import xmlfunc

from ic import datasrc_proto

__version__ = (0, 0, 3, 1)

DEFAULT_OUTPUT_XML_FILENAME = 'output.xml'

CURL_HTTP_404_ERR = 'Error 404 Not Found'
CURL_HTTP_500_ERR = 'Error 500 Not Found'

INBOX_STATE_NAME = 'INBOX'


class icUTMDataSource(datasrc_proto.icDataSourceProto):
    """
    Источник данных УТМ.
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        datasrc_proto.icDataSourceProto.__init__(self, *args, **kwargs)

        # Адрес УТМ
        self.utm_url = kwargs.get('utm_url', None)

        # Где находится утилита CURL с помощью которой происходит взаимодействие с УТМ
        self.curl = kwargs.get('curl', None)

        # Выходная директория для временного хранения загружаемых XML файлов
        self.output_dir = kwargs.get('output_dir', None)

    def get_http(self, url):
        """
        Получить содержание по URL.
        @param url: Адрес запроса.
        @return: Вовращает содержимое XML файла или None в случае ошибки.
        """
        if not (url.startswith('http://') or url.startswith('https://')):
            log.warning(u'Указан не абсолютный адрес <%s> при получении содержания по адресу' % url)
            url = self.utm_url + url
            log.info(u'Преобразуем адрес к абсолютному виду <%s>' % url)
        try:
            output_xml_filename = os.path.join(self.output_dir, DEFAULT_OUTPUT_XML_FILENAME)
            if os.path.exists(output_xml_filename):
                try:
                    log.info(u'Удаление файла <%s>' % output_xml_filename)
                    os.remove(output_xml_filename)
                except:
                    log.fatal(u'Ошибка удаления файла <%s>' % output_xml_filename)
            cmd = '"%s" --output "%s" -X GET %s' % (self.curl, output_xml_filename, url)
            execfunc.exec_shell(cmd)

            content = None
            if os.path.exists(output_xml_filename):
                try:
                    content = xmlfunc.load_xml_content(output_xml_filename)
                except:
                    log.error(u'Ошибка XML файла данных <%s>' % output_xml_filename)
                    self._backup_error_file(output_xml_filename)
                    raise
            else:
                log.warning(u'Не найден выходной файл УТМ <%s>' % output_xml_filename)

            return content
        except:
            log.fatal(u'Ошибка получения содержания УТМ по адресу <%s>' % url)
        return None

    def _backup_error_file(self, src_filename, err_filename=None):
        """
        Сохранить ошибочный файл в папке.
        @param src_filename: Имя исходного ошибочного файла.
        @param err_filename: Имя нового файла.
            Если не определено, то имя генерируется по времени.
        @return: True/False.
        """
        if err_filename is None:
            err_filename = os.path.join(str(self.output_dir),
                                        datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S.err'))
        try:
            if os.path.exists(err_filename):
                os.remove(err_filename)
            shutil.copyfile(src_filename, err_filename)
            return True
        except:
            log.fatal(u'Ошибка сохранения ошибочного файла')
        return False

    def get_content_error(self, content):
        """
        Проверка возвращаемого значение/содержания на ошибки.
        @param content: Возвращаемое значение какой либо операции.
        @return: Текст ошибки, None - нет ошибки.
        """
        if content is None:
            log.warning(u'Не определено содержание для проверки на ошибки')
            return None

        if 'A' not in content:
            log.warning(u'Не корректный формат <%s>' % content)
            return None

        if 'error' in content['A']:
            err_txt = content['A']['error']
            # Отобразить контент для отладки
            log.error(u'Error content: <%s>' % content)
            return err_txt
        return None

    def get_inbox_documents(self):
        """
        Запросить входящие документы.
        """
        if self.cache_state and INBOX_STATE_NAME in self.cache_state:
            return self.cache_state[INBOX_STATE_NAME].values()

        content = self.get_http('/opt/out')
        if content is None:
            log.warning(u'Ошибка определения данных по адресу </opt/out>')
            return None

        if not self.get_content_error(content):
            documents = list()
            if 'A' not in content:
                # Если не ссылка на документ, то это просто его содержание
                documents.append(dict(url=u'',
                                      uuid=str(uuid.uuid4()),
                                      content=content))
            else:
                document_urls = content['A'].get('url', list())
                if type(document_urls) not in (list, tuple):
                    # ВНИМАНИЕ! Может быть только 1 документ
                    # Все равно мы должны обрабатывать список
                    document_urls = [document_urls]

                if not document_urls:
                    log.warning(u'Список входящих документов ЕГАИС УТМ пуст')
                    return documents
                else:
                    #
                    log.debug(u'Обрабатываемые документы. URLs:')
                    for document_url in document_urls:
                        log.debug(u'\t%s' % document_url)

                for document_url in document_urls:
                    if isinstance(document_url, str) or isinstance(document_url, unicode):
                        log.debug(u'Получаем документ URL (str) <%s>' % document_url)
                        document_content = self.get_http(document_url)
                        documents.append(dict(url=document_url,
                                              uuid=str(uuid.uuid4()),
                                              content=document_content))
                    elif isinstance(document_url, dict):
                        log.debug(u'Получаем документ URL (dict) <%s>' % document_url['#text'])
                        document_content = self.get_http(document_url['#text'])
                        documents.append(dict(url=document_url['#text'],
                                              uuid=document_url['@replyId'],
                                              content=document_content))
                    else:
                        log.warning(u'Не обрабатываемый тип адреса документа <%s>' % document_url)

            return documents
        else:
            return None

    def find_inbox_document(self, doc_uuid):
        """
        Найти входящий документ по его UUID.
        @param doc_uuid: UUID документа.
        @return: Словарь содержимого документа или None если документ не найден или ошибка.
        """
        if self.cache_state and INBOX_STATE_NAME in self.cache_state:
            if doc_uuid in self.cache_state[INBOX_STATE_NAME]:
                return self.cache_state[INBOX_STATE_NAME][doc_uuid]
            else:
                log.warning(u'Кеш источника данных <%s>. Документ <%s> не найден во входящих' % (self.name, doc_uuid))
        else:
            content = self.get_http('/opt/out')
            if content:
                document_urls = content['A'].get('url', list())
                if type(document_urls) not in (list, tuple):
                    # ВНИМАНИЕ! Может быть только 1 документ
                    # Все равно мы должны обрабатывать список
                    document_urls = [document_urls]

                if not document_urls:
                    log.warning(u'Список входящих документов пуст')

                for document_url in document_urls:
                    if isinstance(document_url, dict) and document_url['@replyId'] == doc_uuid:
                        document_content = self.get_http(document_url['#text'])

                        # ВНИМАНИЕ! Необходимо кроме содержания запоминать URL и ReplyID документа
                        # иначе нельзя будет идентифицировать документ
                        # return document_content
                        return dict(url=document_url['#text'], uuid=doc_uuid, content=document_content)
                    elif isinstance(document_url, str) or isinstance(document_url, unicode):
                        document_content = self.get_http(document_url)
                        return dict(url=document_url, uuid=doc_uuid, content=document_content)
                log.warning(u'Документ <%s> не найден во входящих' % doc_uuid)
            else:
                log.warning(u'Нет ответа от УТМ')
        return None

    def del_http(self, url):
        """
        Удалит данные по URL на сервере УТМ.
        Когда ответ на запрос обработан его необходимо удалить
        командой вида:
        curl -X DELETE http://localhost:8080/opt/out/ReplyPartner/407
        Регулярное удаление отработанных запросов из списка и сохраненных ответов
        на эти запросы из списка предотвращает безконтрольный рост размера
        базы данных УТМ.
        @param url: Адрес запроса.
        """
        if not (url.startswith('http://') or url.startswith('https://')):
            log.warning(u'Указан не абсолютный адрес <%s> при получении содержания по адресу' % url)
            url = self.utm_url + url
            log.info(u'Преобразуем адрес к абсолютному виду <%s>' % url)
        try:
            output_xml_filename = os.path.join(self.output_dir, DEFAULT_OUTPUT_XML_FILENAME)
            if os.path.exists(output_xml_filename):
                try:
                    log.info(u'Удаление файла <%s>' % output_xml_filename)
                    os.remove(output_xml_filename)
                except:
                    log.fatal(u'Ошибка удаления файла <%s>' % output_xml_filename)

            cmd = '"%s" --output "%s" -X DELETE %s' % (self.curl, output_xml_filename, url)
            execfunc.exec_shell(cmd)

            content = xmlfunc.load_xml_content(output_xml_filename)
            if content is not None:
                # Необходимо проанализировать ошибки
                content = self.valid_content(content)
                return content
        except:
            log.fatal(u'Ошибка удаления данных УТМ по адресу <%s>' % url)
        return None

    def valid_content(self, content):
        """
        Анализ содержания на ошибки.
        @param content: Содержание в текстовом виде.
        """
        if CURL_HTTP_404_ERR in content:
            log.error(u'Http 404')
            log.error(content)
            return None
        elif CURL_HTTP_500_ERR in content:
            log.error(u'Http 500')
            log.error(content)
            return None
        return content

    def diagnostic(self):
        """
        Простая процедура прверки доступа к источнику данных.
        @return: True/False.
        """
        log.debug(u'Диагностика объекта <%s>.<%s>' % (self.__class__.__name__, self.name))

        inbox_docs_uuid = self.get_inbox_doc_uuid()
        if inbox_docs_uuid is None:
            return False

        # log.debug(u'Входящие документы УТМ %s' % inbox_docs)
        for doc_uuid in inbox_docs_uuid:
            log.debug(u'УТМ. Входящие. Документ <%s>' % doc_uuid)
        return True

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

    def _read(self, *values):
        """
        Чтение данных из источника данных.
        @param values: Список читаемых переменных.
        @return: Список прочианных значений.
            Если переменная не найдена или произошла ошибка чтения, то
            вместо значения подставляется None с указанием WARNING в журнале сообщений.
        """
        if not values:
            log.warning(u'Не определены переменные для чтения в <%s>' % self.name)
            values = self.values
            log.debug(u'Переменные взяты из описания источника данных: %s' % values)

        try:
            # Прочитать все документы
            inbox_docs = self.get_inbox_documents()
            if inbox_docs is None:
                return False

            # Регистрация состояния
            if not self.cache_state:
                inbox = dict([(doc.get('uuid', str(uuid.uuid4())), doc) for doc in inbox_docs])
                state = dict([(val, self.gen_code(getattr(self, val))) for val in values])
                # state = self.get_values_as_dict(values)
                state[INBOX_STATE_NAME] = inbox
                self.reg_state(**state)

                self.cache_state = self.state

            return inbox_docs
        except:
            log.fatal(u'Ошибка чтения входящих документов УТМ')
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
            values = self.values
            log.debug(u'Переменные взяты из описания источника данных: %s' % values)

        read_list = self.read(*values)
        result = None
        if read_list is None:
            return None
        elif not read_list and isinstance(read_list, list):
            return dict()
        elif read_list and isinstance(read_list, list):
            result = self.state
        log.debug(u'Результат чтения данных в виде словаря %s' % result)
        return result

    def get_inbox_doc_uuid(self):
        """
        Список UUID входных документов УТМ.
        """
        if self.cache_state and INBOX_STATE_NAME in self.cache_state:
            read_list = self.cache_state[INBOX_STATE_NAME].values()
        else:
            read_list = self.get_inbox_documents()

        result = list()
        if read_list and isinstance(read_list, list):
            result = [doc.get('uuid', str(uuid.uuid4())) for doc in read_list]
            log.debug(u'Список UUID входных документов УТМ %s' % result)
        return result

    def parse_inbox_doc(self, doc_uuid, str_replaces=None, **content_links):
        """
        Произвести сборку данных входных документов по запрашиваемым данным.
        @param doc_uuid: UUID необходимого входного документа.
        @param str_replaces: Словарь замены в строковых значениях.
            Если словарь не определен замены не производятся.
        @param content_links: Словарь запрашиваемых данных у каждого документа.
            Например:
            {
                'error': 'A/error',
                'transport_uuid': 'A/url'
            }
        @return: Список заполненных словарей запрашиваемых данных для документа.
        """
        if doc_uuid is None:
            log.warning(u'УТМ. Не определен UUID документа при запросе данных')
            return dict([(name, None) for name in content_links.keys()])

        doc_content = self.find_inbox_document(doc_uuid)
        if doc_content:
            result = dict()
            for name, link in content_links.items():
                value = xmlfunc.get_xml_content_by_link(doc_content, link)
                if str_replaces and type(value) in (str, unicode):
                    for replace_src, replace_dst in str_replaces.items():
                        value = value.replace(replace_src, replace_dst)
                result[name] = value
            return result
        else:
            log.warning(u'УТМ. Ошибка чтения содержимого документа <%s>' % doc_uuid)

        return None

    def parse_inbox_docs(self, doc_uuids=None, str_replaces=None, **content_links):
        """
        Произвести сборку данных входных документов по запрашиваемым данным.
        @param doc_uuids: Список UUID необходимых входных документов.
            Если None, то обрабатываются все документы.
        @param str_replaces: Словарь замены в строковых значениях.
            Если словарь не определен замены не производятся.
        @param content_links: Словарь запрашиваемых данных у каждого документа.
            Например:
            {
                'error': 'A/error',
                'transport_uuid': 'A/url'
            }
        @return: Список заполненных словарей запрашиваемых данных для каждого документа.
        """
        if doc_uuids is None:
            doc_uuids = self.get_inbox_doc_uuid()

        result = list()
        for doc_uuid in doc_uuids:
            if not doc_uuid:
                log.warning(u'УТМ. Не корректный UUID запрашиваемого документа <%s>' % doc_uuid)
                continue
            doc = self.parse_inbox_doc(doc_uuid, str_replaces=str_replaces, **content_links)
            if doc is not None:
                result.append(doc)
        log.debug(u'УТМ. Сборка данных входных документов %s' % result)
        return result
