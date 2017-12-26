#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
Менеджер управления настройками программы.
"""

import os
import os.path
import copy

from ic.utils import log
from ic.utils import ini
from ic.utils import utils
from ic import config

__version__ = (0, 0, 1, 2)


class icSettingsManager(object):
    """
    Менеджер управления настройками программы.
    """
    def __init__(self, *args, **kwargs):
        """
        Конструктор.
        """
        # Имя INI файла настройки
        self.ini_filename = None

    def genINIFileName(self):
        """
        Генерация имени настроечного INI файла.
        """
        if not self.ini_filename:
            cur_dir = os.path.dirname(os.path.dirname(__file__))
            if not cur_dir:
                cur_dir = os.getcwd()
            self.ini_filename = os.path.normpath(os.path.join(cur_dir, config.DEFAULT_INI_FILENAME))
        return self.ini_filename

    def printSettings(self, dSettings):
        """
        Вывод на экран текущих настроек для отладки.
        """
        for section in dSettings.keys():
            log.info(section)
            for name, value in dSettings[section].items():
                log.info('\t%s\t:\t%s' % (name, value))

    def loadSettings(self, sINIFileName=None):
        """
        Загрузка настроек из INI файла.
        @type sINIFileName: C{string}
        @param sINIFileName: Полное имя конфигурационного файла.
            Если None, то генерируется.
        @return: True - загрузка параметров прошла успешно,
            False - загрузка не прошла по какой-либо причине.
        """
        if sINIFileName is None:
            sINIFileName = self.genINIFileName()

        if os.path.exists(sINIFileName):
            settings = ini.INI2Dict(sINIFileName)
            settings = ini.toUnicodeINIValues(settings)
            if settings:
                # Инициализация переменных настроек
                self.loadSectionList(settings, 'OPTIONS', 'sources', 'SOURCES')
                self.loadSectionList(settings, 'OPTIONS', 'destinations', 'DESTINATIONS')
                self.loadSectionList(settings, 'OPTIONS', 'queue', 'QUEUE')

                if 'run_mode' in settings.get('OPTIONS', dict()):
                    config.set_cfg_var('RUN_MODE', settings.get('OPTIONS', dict()).get('run_mode', 'debug'))

                config.set_cfg_var('TICK_PERIOD', settings.get('OPTIONS', dict()).get('tick', 300))

                log.info('LOAD SETTINGS')
                if utils.isDebugMode():
                    self.printSettings(settings)

                return True
            else:
                log.warning('Don\'t define settings. Ini file name: %s' % sINIFileName)
        return False

    def loadSectionList(self, ini_settings, section, name, cfg_name):
        """
        Загрузка списка секций из INI файла.
        @param ini_settings: Словарь содержания INI файла.
        @param section: Секция источника.
        @param name: Наименование параметра источника данных запрашиваемого списка секций.
        @param cfg_name: Имя списка секций в сонфигурационном файле.
        @return: True/False.
        """
        ini_names = ini_settings.get(section, dict()).get(name, list())
        cfg_sections = list()
        for ini_name in ini_names:
            # cfg_section = ini_settings.get(ini_name, dict())
            cfg_section = self.buildSection(ini_settings, ini_name)
            cfg_section['name'] = ini_name
            log.debug(u'Собранная секция %s' % cfg_section.keys())
            cfg_sections.append(cfg_section)
        config.set_cfg_var(cfg_name, cfg_sections)

    def buildSection(self, ini_settings, ini_name):
        """
        Собрать полное описание секции с учетом ключа parent.
        Через ключ parent можно наследовать описание секции.
        @param ini_settings: Словарь содержания INI файла.
        @param ini_name: Наименование запрашиваемой секции.
        @return: Словарь секции дополненный переменными из секции указанной в parent.
            Сборка данных производиться рекурсивно.
        """
        section = copy.deepcopy(ini_settings.get(ini_name, dict(name=ini_name)))
        if 'parent' not in section:
            return section
        elif not section['parent']:
            del section['parent']
            return section
        elif section['parent'] not in ini_settings:
            log.warning(u'Запрашиваемая секция <%s> как родительская для <%s> не найдена' % (section['parent'], ini_name))
            del section['parent']
            return section
        else:
            if type(section['parent']) in (str, unicode):
                parent_section = self.buildSection(ini_settings, section['parent'])
                parent_section.update(section)
                del parent_section['parent']
                return parent_section
            elif type(section['parent']) in (list, tuple):
                result_section = dict()
                for parent_section_name in section['parent']:
                    parent_section = self.buildSection(ini_settings, parent_section_name)
                    result_section.update(parent_section)
                result_section.update(section)
                del result_section['parent']
                return result_section
        return section

    def saveSettings(self, sINIFileName=None):
        """
        Сохранение настрек в INI файле.
        @type sINIFileName: C{string}
        @param sINIFileName: Полное имя конфигурационного файла.
            Если None, то генерируется.
        @return: True - запись параметров прошла успешно,
            False - запись не прошла по какой-либо причине.
        """
        if sINIFileName is None:
            sINIFileName = self.genINIFileName()

        settings = dict()
        # Сохранение настроечных переменных в словаре настроек

        log.info('SAVE SETTINGS')
        if utils.isDebugMode():
            self.printSettings(settings)

        return ini.Dict2INI(settings, sINIFileName)

    def existsINIFile(self, sINIFileName=None):
        """
        Проверка существования файла настройки.
        @type sINIFileName: C{string}
        @param sINIFileName: Полное имя конфигурационного файла.
            Если None, то генерируется.
        """
        if sINIFileName is None:
            sINIFileName = self.genINIFileName()

        return os.path.exists(sINIFileName)

