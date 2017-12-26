#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Функции работы с XML файлами и XML представлениями.
"""

import os
import os.path
from ic.contrib import xmltodict
from ic.contrib import dicttoxml
from ic.utils import log
from ic.convert import simple_dict2xml

__version__ = (0, 0, 2, 3)


def load_xml_content(xml_filename, is_change_keys=True):
    """
    Загрузить содержимое XML файла в словарно списковую структуру.
    @param xml_filename: Полное имя XML файла.
    @param is_change_keys: Произвести автоматическую замену ключей на короткие.
    @return: Словарно-списковая структура содержания XML файла.
        Или None в случае ошибки.
    """
    if not os.path.exists(xml_filename):
        log.warning(u'XML файл <%s> не найден' % xml_filename)
        return None

    log.info(u'Загрузка содержимого файла <%s>' % xml_filename)
    xml_file = None
    try:
        xml_file = open(xml_filename, 'r')
        xml_txt = xml_file.read()
        xml_file.close()
    except:
        if xml_file:
            xml_file.close()
        log.fatal(u'Ошибка загрузки содержимого XML файла <%s>' % xml_filename)
        return None

    if not xml_txt.strip():
        log.error(u'Файл <%s> пустой' % xml_filename)
        return dict()

    data = xmltodict.parse(xml_txt)
    if is_change_keys:
        data = change_keys_doc(data)
    return data


def change_keys_doc(xml_document):
    """
    Сократить ключи документа.
    @param xml_document: Содержание XML документа.
    @return: Содержание документа с короткими ключами.
    """
    result = dict()
    if isinstance(xml_document, dict):
        for key in xml_document.keys():
            # Взять только часть ключа с <:> и до конца
            new_key = key.split(':')[-1]
            if isinstance(xml_document[key], xmltodict.OrderedDict):
                result[new_key] = change_keys_doc(xml_document[key])
            elif isinstance(xml_document[key], list):
                result[new_key] = list()
                for doc_element in xml_document[key]:
                    result[new_key].append(change_keys_doc(doc_element))
            else:
                result[new_key] = xml_document[key]
    else:
        log.warning(u'Не корректное содержимое XML документа <%s>' % xml_document)
        return xml_document
    return result

# Разделитель пути до содержимого XML файла
XML_CONTENT_LINK_DELIMETER = '/'


def get_xml_content_by_link(xml_content, link):
    """
    Получить часть содержимого XML файла по пути.
    @param xml_content: Сродержимое XML файла.
    @param link: Запрашиваемый путь. Может быть представлен в виде списка или строки.
        Например:
        root/Documents/1/Document/Title/value
    @return: Часть содержимого или None если по этому пути ничего не найдено.
    """
    log.debug(u'Получение содержимого XML файла по пути %s' % link)

    if type(link) in (str, unicode):
        link = link.split(XML_CONTENT_LINK_DELIMETER)

    if type(link) not in (list, tuple):
        log.error(u'Не корректный тип пути <%s> до содержимого XML файла' % type(link))
        return None

    if not link:
        return xml_content

    if link[0] not in xml_content:
        log.warning(u'Не найден путь %s в содержимом %s XML файла' % (link, xml_content.keys()))
        return None
    elif link[0] in xml_content:
        return get_xml_content_by_link(xml_content[link[0]], link[1:])

    return None


def save_xml_content(xml_filename, data, is_rewrite=True):
    """
    Записать словарно списковую структуру в XML файл.
    @param xml_filename: Полное имя XML файла.
    @param data: Словарно-списковая структура содержания XML файла.
    @param is_rewrite: Перезаписать результирующий файл, если необходимо?
    @return: True/False.
    """
    if os.path.exists(xml_filename) and not is_rewrite:
        log.warning(u'Запрет на перезапись. Файл <%s> уже существует.' % xml_filename)
        return False

    # Сама конвертация словаря в текст
    if isinstance(data, list):
        xml_txt = dicttoxml.dicttoxml(data, root=True,
                                      custom_root='root',
                                      ids=False, attr_type=False)
    elif isinstance(data, dict):
        root_key = data[data.keys()[0]]
        xml_txt = dicttoxml.dicttoxml(data, root=False,
                                      custom_root=root_key,
                                      ids=False, attr_type=False)
    else:
        log.warning(u'Не корректный тип данных <%s> для записи в XML файл' % type(data))
        return False

    xml_file = None
    try:
        xml_file = open(xml_filename, 'w')
        xml_file.write(xml_txt)
        xml_file.close()
        return True
    except:
        if xml_file:
            xml_file.close()
        log.fatal(u'Ошибка записи в файл <%s>' % xml_filename)
    return False


def save_simple_xml_content(xml_filename, data, is_rewrite=True, tag_filter=None):
    """
    Записать словарно списковую структуру в XML файл.
    Самая простая реализация.
    @param xml_filename: Полное имя XML файла.
    @param data: Словарно-списковая структура содержания XML файла.
    @param is_rewrite: Перезаписать результирующий файл, если необходимо?
    @param tag_filter: Словарь фильтра тегов,
        определяющий список и порядок дочерних тегов для
        каждого тега.
        Порядок тегов важен для XML, поэтому введен этот фильтр.
    @return: True/False.
    """
    if os.path.exists(xml_filename) and not is_rewrite:
        log.warning(u'Запрет на перезапись. Файл <%s> уже существует.' % xml_filename)
        return False

    xml_file = None
    try:
        # Начать запись
        xml_file = open(xml_filename, 'wt')
        xml_writer = simple_dict2xml.icSimpleDict2XmlWriter(data, xml_file)
        xml_writer.startDocument()
        xml_writer.startWrite(tag_filter=tag_filter)

        # Закончить запись
        xml_writer.endDocument()
        xml_file.close()
        return True
    except:
        if xml_file:
            xml_file.close()
        log.fatal(u'Ошибка записи в файл <%s>' % xml_filename)
    return False

