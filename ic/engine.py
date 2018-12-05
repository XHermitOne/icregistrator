#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
Модуль основного движка регистратора.
"""

import os
import os.path
import time
import datetime
from ic import config
from ic.utils import log
from ic.utils import keyboardfunc
from ic.utils import journal

from . import settings
from . import src
from . import dst

__version__ = (0, 0, 4, 1)

# Сигнатура ссылки
LINK_SIGNATURE = u'link:'

# Разделитель ссылки
LINK_DELIMETER = u'.'


class icRegistratorProto(object):
    """
    Абстрактный класс движка регистратора.
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        # Менеджер настроек
        self.settings_manager = settings.icSettingsManager()

        # Словарь зарегистрированных объектов
        self.objects = dict()

        # После создания объекта прописываем его в конфиге для доступа из прикладного функционала
        config.set_cfg_var('ENGINE', self)

    def init_settings(self):
        """
        Проинициализировать конфигурационные переменные в соответствии с настройками.
        @return: True/False.
        """
        ini_filename = config.get_cfg_var('SETTINGS_FILENAME')
        if ini_filename and not os.path.exists(ini_filename):
            log.warning(u'Файл настроек <%s> не найден. Используется файл настроек по умолчанию' % ini_filename)
            ini_filename = None
        return self.settings_manager.loadSettings(ini_filename)

    def reg_object(self, obj):
        """
        Регистрация нового объекта в словаре внутренних объектов.
        Регистрация производиться по имени объекта.
        @param obj: Регистрируемый объект.
        @return: True -  регистрация прошла успешно / False - ошибка.
        """
        if hasattr(obj, 'name'):
            # Регистрация по имени
            name = getattr(obj, 'name')
            self.objects[name] = obj
            return True
        else:
            log.warning(u'Не возможно зарегистрировать объект класса <%s>' % obj.__class__.__name__)
        return None

    def find_object(self, obj_name):
        """
        Поиск объекта в зарегистрированных по имени.
        @param obj_name: Имя объекта.
        @return: Объект или None если объект с таким именем не найден.
        """
        if obj_name in self.objects:
            return self.objects[obj_name]
        log.warning(u'Объект <%s> не найден среди зарегистрированных %s' % (obj_name, self.objects.keys()))
        return None

    def create_src(self, **properties):
        """
        Метод создания объекта источника данных с инициализацией его свойств.
        @param properties: Словарь свойств источника данных.
        @return: Объект источника данных или None в случае ошибки.
        """
        # Сначала в любом случае определяем тип источника данных
        if 'type' in properties:
            src_typename = properties['type']
            src_class = src.DATA_SOURCES.get(src_typename, None)
            if src_class is None:
                log.error(u'Ошибка создания объекта источника данных. Тип <%s> не зарегистрирован в системе как источник данных' % src_typename)
            else:
                try:
                    log.info(u'Создание объекта источника данных <%s>' % properties.get('name', src_class.__name__))
                    src_obj = src_class(parent=self, **properties)
                    # Регистрируем новый объект в словаре внутренних объектов
                    self.reg_object(src_obj)
                    return src_obj
                except:
                    log.fatal(u'Ошибка создания объекта источника данных')
        else:
            name = properties.get('name', u'')
            log.error(u'Ошибка создания объекта источника данных. Не определен тип <%s>' % name)
        return None

    def create_dst(self, **properties):
        """
        Метод создания объекта приемника данных с инициализацией его свойств.
        @param properties: Словарь свойств приемника данных.
        @return: Объект приемника данных или None в случае ошибки.
        """
        # Сначала в любом случае определяем тип источника данных
        if 'type' in properties:
            dst_typename = properties['type']
            dst_class = dst.DATA_DESTINATIONS.get(dst_typename, None)
            if dst_class is None:
                log.error(u'Ошибка создания объекта приемника данных. Тип <%s> не зарегистрирован в системе как источник данных' % dst_typename)
            else:
                try:
                    log.info(u'Создание объекта получателя данных <%s>' % properties.get('name', dst_class.__name__))
                    dst_obj = dst_class(parent=self, **properties)
                    # Регистрируем новый объект в словаре внутренних объектов
                    self.reg_object(dst_obj)
                    return dst_obj
                except:
                    log.fatal(u'Ошибка создания объекта приемника данных')
        else:
            name = properties.get('name', u'')
            log.error(u'Ошибка создания объекта приемника данных. Не определен тип <%s>' % name)
        return None

    def create(self, **properties):
        """
        Создание объекта. По значениям свойств функция сама определяет какого типа будет объект.
        @param properties: Словарь свойств объекта.
        @return: Объект приемника данных или None в случае ошибки.
        """
        name = properties.get('name', u'')

        # Сначала определяем тип объекта
        if 'type' in properties:
            type_name = properties['type']
        else:
            log.error(u'Ошибка создания объекта. Не определен тип <%s>' % name)
            return None

        # Сначала проверяем является ли объект источником данных
        if type_name in src.DATA_SOURCES:
            return self.create_src(**properties)
        # Сначала проверяем является ли объект источником данных
        if type_name in dst.DATA_DESTINATIONS:
            return self.create_dst(**properties)
        log.warning(u'Тип <%s> объекта <%s> не зарегистрирован среди источнико или приемников данных' % (type_name, name))
        return None

    def is_link(self, value):
        """
        Проверка является ли значение ссылкой.
        @param value: Проверяемое значение.
        @return: True - это ссылка, False - нет.
        """
        return type(value) in (str, unicode) and value.lower().startswith(LINK_SIGNATURE)

    def is_link_func(self, link):
        """
        В ссылке указан вызов метода/функции?
        @param link: Строковая ссылка.
        @return: True - да это вызов функции. False - это вызов переменной
        """
        obj_name, val_name = link.split(LINK_DELIMETER)
        return u'(' in val_name and u')' in val_name and val_name.strip().endswith(u')')

    def get_value_by_link(self, link):
        """
        Получить значение внутренней переменной по ссылке.
        @param link: Строковая ссылка в формате:
            ИМЯ_ОБЪЕКТА.имя_переменной или
            ИМЯ_ОБЪЕКТА.имя_функции(аргументы функции).
        @return: Значение внутренней переменной или None если по этой ссылке переменная или объект не найдены.
        """
        if link.startswith(LINK_SIGNATURE):
            # Убрать сигнатуру из обработки
            link = link[len(LINK_SIGNATURE):].strip()

        try:
            # Разделяем ссылку на имя объекта и имя переменной
            obj_name, val_name = link.split(LINK_DELIMETER)

            # Определение объекта
            obj = self.objects.get(obj_name, None)
            if obj is None:
                log.warning(u'Не найден объект <%s> среди зарегистрированных' % obj_name)
                return None

            if not self.is_link_func(link):
                # Определение значения переменной
                value = obj.state.get(val_name, None)
                if value is None:
                    log.warning(u'Не найдена переменная <%s> в объекте <%s>' % (val_name, obj_name))
                    return None
            else:
                # Это вызов функции
                value = None
                try:
                    value = eval(u'obj.%s' % val_name)
                except:
                    log.fatal(u'Ошибка вызова метода <%s.%s>' % (obj_name, val_name))
            return value
        except:
            log.fatal(u'Ошибка получения значения внутренней переменной по ссылке <%s>' % link)
        return None


class icRegistrator(icRegistratorProto):
    """
    Движок регистратора.
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        icRegistratorProto.__init__(self, *args, **kwargs)

    def clear_all_state_chaches(self, *objects):
        """
        Сбросить все кеши в объектах
        @param objects: Список обрабатываемых объектов.
        @return: True/False.
        """
        if not objects:
            log.warning(u'Не определены объекты для сброса кеша состояния')
            return False

        result = True
        for obj in objects:
            try:
                obj.clear_state_cache()
                result = result and True
            except:
                log.fatal(u'Ошибка сброса кеша в объекте <%s>' % obj)
                result = False
        return result

    def run_tick(self, n_tick=1):
        """
        Запуск всех объектов для выполнения 1 тика.
        @param n_tick: Номер текущего тика.
        @return: True/False.
        """
        try:
            config.set_cfg_var('TICK_DT_START', datetime.datetime.now())
            # ВНИМАНИЕ! Необходимо с начале каждого тика надо создавать объекты
            # чтобы не контролировать актуальность их состояния
            log.info(u'Создание объектов...')
            src_objects = list()
            for properties in config.SOURCES:
                # Создаем объекты источников данных
                obj = self.create(**properties)
                if obj:
                    src_objects.append(obj)
            dst_objects = list()
            for properties in config.DESTINATIONS:
                # Создаем объекты получателей данных
                obj = self.create(**properties)
                if obj:
                    dst_objects.append(obj)

            if not config.QUEUE:
                log.info(u'Порядок обработки штатный')
                log.info(u'Начало обработки...')
                journal.write_msg(u'Начало обработки...')
                for src_object in src_objects:
                    log.info(u'Чтение данных из <%s>' % src_object.name)
                    journal.write_msg(u'\tЧтение данных из <%s>' % src_object.description)
                    src_object.read_as_dict()
                for dst_object in dst_objects:
                    log.info(u'Запись данных в <%s>' % dst_object.name)
                    journal.write_msg(u'\tЗапись данных в <%s>' % dst_object.description)
                    dst_object.write_as_dict()
                log.info(u'...Конец обработки [%d]' % n_tick)
                journal.write_msg(u'...Конец обработки')
            else:
                log.info(u'Порядок обработки задан явно %s' % config.QUEUE)
                log.info(u'Начало обработки...')
                journal.write_msg(u'Начало обработки...')
                for obj_properties in config.QUEUE:
                    obj_name = obj_properties['name']
                    obj = self.find_object(obj_name)
                    if obj:
                        obj_type = obj_properties['type']
                        if obj_type in src.DATA_SOURCES.keys():
                            # Это источник данных
                            log.info(u'Чтение данных из <%s>' % obj.name)
                            journal.write_msg(u'\tЧтение данных из <%s>' % obj.description)
                            obj.read_as_dict()
                        elif obj_type in dst.DATA_DESTINATIONS.keys():
                            # Это получатель данных
                            log.info(u'Запись данных в <%s>' % obj.name)
                            journal.write_msg(u'\tЗапись данных в <%s>' % obj.description)
                            obj.write_as_dict()
                        else:
                            # Вообще не определенный тип
                            log.warning(u'Не поддерживаемый тип <%s> объекта <%s>' % (obj_type, obj_name))
                log.info(u'...Конец обработки [%d]' % n_tick)
                journal.write_msg(u'...Конец обработки')

            # Сбросить кеш состояния в конце такта
            # obj_list = src_objects + dst_objects
            # self.clear_all_state_chaches(*obj_list)
            return True
        except:
            log.fatal(u'Ошибка выполнения тика [%d]' % n_tick)
        return False

    def run(self, mode=None):
        """
        Основная процедура запуска регистрации.
        @param mode: Режим запуска регистратора.
        @return: True/False.
        """
        # Проинициализировать конфигурационные переменные в соответствии с настройками.
        self.init_settings()

        if mode is None:
            mode = config.get_cfg_var('RUN_MODE')

        if mode == config.RUN_MODE_SINGLE:
            # Одноразовый запуск
            self.run_tick()
            config.set_cfg_var('TICK_DT_STOP', datetime.datetime.now())

        elif mode == config.RUN_MODE_LOOP:
            # Запуск регистратора в цикле

            # Запуск цикла обработки
            do_exit = False
            tick = config.get_cfg_var('TICK_PERIOD')
            log.info(u'Период цикла обработки: <%d>...' % tick)
            i_tick = 1
            while not do_exit:
                start_tick = time.time()
                end_tick = start_tick + tick

                self.run_tick(i_tick)

                if tick > 0:
                    log.warning(u'Для выхода нажмите <ESC>')
                    cur_time = time.time()
                    while end_tick > cur_time:
                        ch_key = keyboardfunc.getchAsync()
                        if keyboardfunc.same_key(ch_key, keyboardfunc.ESC_KEY):
                            do_exit = True
                            log.info(u'Выход из цикла обработки')
                            break
                        cur_time = time.time()
                        # log.debug(u'test tick %d : %d' % (cur_time, end_tick))
                else:
                    log.warning(u'Для выхода нажмите <Ctrl+C>')

                config.set_cfg_var('TICK_DT_STOP', datetime.datetime.now())
                log.info(u'...Конец периода цикла обработки [%d]' % i_tick)
                i_tick += 1

        elif mode == config.RUN_MODE_SRC_DIAGNOSTIC:
            # Запуск регистратора в режиме диагностики источников данных
            self.do_diagnostic(config.SOURCES)

        elif mode == config.RUN_MODE_DST_DIAGNOSTIC:
            # Запуск регистратора в режиме диагностики получателя данных
            self.do_diagnostic(config.DESTINATIONS)

        elif mode == config.RUN_MODE_DEBUG:
            # Запуск в режиме отладки
            for src_properties in config.SOURCES:
                src_obj = self.create_src(**src_properties)
                if src_obj:
                    result = src_obj.read_as_dict(*src_obj.values)
                    log.info(u'Результат чтения данных из контроллера %s' % result)
        else:
            log.warning(u'Режим запуска регистратра <%s> не поддерживается системой' % mode)
        return False

    def do_diagnostic(self, property_obj_list):
        """
        Произвести диагностику объектов.
        @param property_obj_list: Список свойств объектов.
            В нашем случае это или config.SOURCES или config.DESTIONATIONS.
        """
        for properties in property_obj_list:
            obj = self.create(**properties)
            if obj:
                obj.diagnostic()
