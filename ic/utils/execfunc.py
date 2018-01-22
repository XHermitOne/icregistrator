#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль функций выполнения запросов и методов пользователя.
"""

# Дополнительно импортируемые модули для создания окружения для выполнения блоков кода
# vvvvvvvvvvvvvvv
import uuid
import datetime
# ^^^^^^^^^^^^^^^

import os
import os.path
import sys
import imp
import locale
from . import log

__versiom__ = (0, 0, 4, 2)

# Сигнатуры блоков кода
PY_SIGNATURE = u'python:'
FUNC_SIGNATURE = u'func:'
CMD_SIGNATURE = u'cmd:'
SHELL_SIGNATURE = u'shell:'
EXEC_SIGNATURES = (PY_SIGNATURE, FUNC_SIGNATURE, CMD_SIGNATURE, SHELL_SIGNATURE)


def loadSource(name, path):
    """
    Возвращает загруженный модуль.

    @type name: C{string}
    @param name: Имя модуля.
    @type path: C{string}
    @param path: Полный путь до модуля.
    """
    f = open(path)
    mod = imp.load_source(name, path, f)
    f.close()
    return mod


def unLoadSource(name):
    """
    Выгрузить модуль.
    @type name: C{string}
    @param name: Имя модуля.
    """
    if name in sys.modules:
        del sys.modules[name]
        return True
    return False


def reLoadSource(name, path=None):
    """
    Перезагрузить модуль.
    @type name: C{string}
    @param name: Имя модуля.
    @type path: C{string}
    @param path: Полный путь до модуля.
    """
    if path is None:
        if name in sys.modules:
            py_file_name = sys.modules[name].__file__
            py_file_name = os.path.splitext(py_file_name)[0]+'.py'
            path = py_file_name
        else:
            log.warning(u'Module <%s> not loaded' % name)
            return None
    unLoadSource(name)
    return loadSource(name, path)


def exec_func(func_code='', bReImport=False, name_space=None, kwargs=None):
    """
    Выполнить блок кода функции.
    @type func_code: C{string}
    @param func_code: Блок кода.
        Блок кода - строка в формате:
            ИмяПакета.ИмяМодуля.ИмяФункции(аргументы).
    @type bReImport: C{bool}
    @param bReImport: Переимпортировать модуль функции?
    @type name_space: C{dictionary}
    @param name_space: Пространство имен.
    @type kwargs: C{dictionary}
    @param kwargs: Дополнительные аргументы функции.
    """
    result = None

    # Подготовить пространство имен
    if name_space is None or not isinstance(name_space, dict):
        name_space = {}

    func_import = func_code.split('(')[0].split('.')
    func_mod = '.'.join(func_import[:-1])

    if bReImport:
        unLoadSource(func_mod)

    # Импортирование модуля
    if func_mod:
        import_str = 'import ' + func_mod
        try:
            exec import_str
        except:
            log.error(u'Import module error <%s>' % import_str)
            raise

    # Добавить локальное пространство имен
    name_space.update(locals())

    if kwargs:
        if isinstance(kwargs, dict):
            name_space.update(kwargs)
        else:
            log.warning(u'Не поддерживаемый тип <%s> дополнительных аргументов функции <%s>' % (type(kwargs), func_code))

    # Выполнение функции
    try:
        result = eval(func_code, globals(), name_space)
    except:
        log.error(u'Ошибка выполнения блока кода функции <%s>' % func_code)
        raise

    return result


def exec_python(python_code):
    """
    Выполнение кода Python.
    @param python_code: Блок кода Pythonю
    @return: Результат выполнения блока кода Python.
    """
    python_code = python_code.strip()
    if not python_code:
        log.warning(u'Python. Пустой блок кода')
        return None

    try:
        log.debug(u'Выполнение блока кода Python <%s>' % python_code)
        return eval(python_code)
    except:
        log.fatal(u'Ошибка выполнения блока кода Python <%s>' % python_code)
    return None

# Разделитель комманд
CMD_DELIMETER = u'{+}'
# Кодировка коммандной оболочки по умолчанию
CMD_ENCODING = sys.stdout.encoding if sys.platform.startswith('win') else locale.getpreferredencoding()


def exec_cmd(cmd):
    """
    Выполнение комманды опереционной системы.
    Комманды могут быть разделены разделителем CMD_DELIMETER.
    В этом случае они выполняются последовательно.
    @param cmd: Комманды ОС.
    @return: True/False.
    """
    cmd = cmd.strip()
    if not cmd:
        log.warning(u'Command. Пустой блок кода')
        return None

    if type(cmd) not in (str, unicode):
        return None

    commands = cmd.split(CMD_DELIMETER)
    result = True
    for command in commands:
        command = command.strip()
        try:
            log.debug(u'Выполнение команды ОС <%s>' % command)
            if isinstance(command, unicode):
                # ВНИМАНИЕ! Комманды выполняются в контексте консоли, поэтому должны быть перекодированы в
                # консольную кодировку перед выполнением
                command = command.encode(CMD_ENCODING)
            os.system(command)
            result = result and True
        except:
            log.fatal(u'Ошибка выполнения комманды ОС <%s>' % command)
            result = False
    return result

# Символ перевода каретки
EOL = '\r\n' if sys.platform.startswith('win') else '\n'


def exec_shell(cmd, auto_remove_cmd_file=True):
    """
    Выполнение комманды опереционной системы через создание коммандного файла и запуск его в шелл.
    Комманды могут быть разделены разделителем CMD_DELIMETER.
    В этом случае они выполняются последовательно.
    @param cmd: Комманды ОС.
    @param auto_remove_cmd_file: Произвести автоматическое удаление коммандного файла после выполнения?
    @return: True/False.
    """
    if type(cmd) not in (str, unicode):
        return None

    tmp_cmd_filename = os.tempnam()+('.bat' if sys.platform.startswith('win') else '.sh')
    commands = [command.strip() + EOL for command in cmd.split(CMD_DELIMETER)]

    is_command = max([bool(command.strip()) for command in commands])
    if not is_command:
        log.warning(u'Shell. Пустой блок кода')
        return None

    log.info(u'Создание коммандного файла <%s>:' % tmp_cmd_filename)
    for cmd in commands:
        log.info(u'\t%s' % cmd)

    # Если файл выполняется в коммандной оболочке,
    # то и кодировка должна быть в кодировке коммандной оболочки
    commands = [command.encode(log.DEFAULT_ENCODING) if isinstance(command, unicode) else command for command in commands]
    # log.debug(u'Список комманд %s' % commands)
    result = True
    tmp_cmd_file = None
    try:
        tmp_cmd_file = open(tmp_cmd_filename, 'w+')
        tmp_cmd_file.writelines(commands)
        tmp_cmd_file.close()
    except:
        if tmp_cmd_file:
            tmp_cmd_file.close()
        log.fatal(u'Ошибка создания коммандного файла <%s> для выполнения комманды ОС <%s>' % (tmp_cmd_filename, cmd))
        result = False

    if result:
        if not os.path.exists(tmp_cmd_filename):
            log.warning(u'Коммандный файл <%s> не найден' % tmp_cmd_filename)
            result = False
        else:
            # Выполнить коммандный файл
            if sys.platform.startswith('win'):
                cmd = '"%s"' % tmp_cmd_filename
            else:
                cmd = 'sh "%s"' % tmp_cmd_filename
            result = exec_cmd(cmd)
            # После выполнения удалить временный коммандный файл
            if auto_remove_cmd_file:
                try:
                    log.info(u'Удаление файла <%s>' % tmp_cmd_filename)
                    os.remove(tmp_cmd_filename)
                except:
                    log.fatal(u'Ошибка удаления файла <%s>' % tmp_cmd_filename)

    return result


def is_code_block(txt):
    """
    Проверка является ли строка/текст блоком кода.
    Текст должен начинаться с сигнатуры блока кода если это блок кода.
    @param txt: Проверяемый текст.
    @return: True/False.
    """
    if type(txt) not in (str, unicode):
        # Если это вообще не текст, то и не блок кода
        return False
    return max([txt.startswith(signature) for signature in EXEC_SIGNATURES])


def is_code_python(txt):
    """
    Проверка является ли строка/текст блоком кода.
    Текст должен начинаться с сигнатуры блока кода если это блок кода.
    @param txt: Проверяемый текст.
    @return: True/False.
    """
    if type(txt) not in (str, unicode):
        # Если это вообще не текст, то и не блок кода
        return False
    return txt.startswith(PY_SIGNATURE)


def is_code_func(txt):
    """
    Проверка является ли строка/текст блоком кода.
    Текст должен начинаться с сигнатуры блока кода если это блок кода.
    @param txt: Проверяемый текст.
    @return: True/False.
    """
    if type(txt) not in (str, unicode):
        # Если это вообще не текст, то и не блок кода
        return False
    return txt.startswith(FUNC_SIGNATURE)


def is_code_cmd(txt):
    """
    Проверка является ли строка/текст блоком кода.
    Текст должен начинаться с сигнатуры блока кода если это блок кода.
    @param txt: Проверяемый текст.
    @return: True/False.
    """
    if type(txt) not in (str, unicode):
        # Если это вообще не текст, то и не блок кода
        return False
    return txt.startswith(CMD_SIGNATURE)


def is_code_shell(txt):
    """
    Проверка является ли строка/текст блоком кода.
    Текст должен начинаться с сигнатуры блока кода если это блок кода.
    @param txt: Проверяемый текст.
    @return: True/False.
    """
    if type(txt) not in (str, unicode):
        # Если это вообще не текст, то и не блок кода
        return False
    return txt.startswith(SHELL_SIGNATURE)


def exec_code_block(code_block):
    """
    Выполнение блока кода.
    В блоке кода должна присутствовать сигнатура для определения метода выполнения блока кода.
    @param code_block: Строка блока кода с сигнатурой.
    @return: Результат выполнения блока кода.
    """
    if not is_code_block(code_block):
        # Это не блок кода
        log.error(u'<%s> не является блоком кода' % str(code_block))
        return None

    if code_block.startswith(PY_SIGNATURE):
        # Обработка блоков кода Python
        code = code_block[len(PY_SIGNATURE):].strip()
        return exec_python(code)
    elif code_block.startswith(FUNC_SIGNATURE):
        # Обработка блоков кода функций
        code = code_block[len(FUNC_SIGNATURE):].strip()
        return exec_func(code)
    elif code_block.startswith(CMD_SIGNATURE):
        # Обработка блоков кода комманд ОС
        code = code_block[len(CMD_SIGNATURE):].strip()
        return exec_cmd(code)
    elif code_block.startswith(SHELL_SIGNATURE):
        # Обработка блоков кода комманд ОС через создание командного файла
        code = code_block[len(SHELL_SIGNATURE):].strip()
        return exec_shell(code)
    else:
        log.warning(u'Не определена сигнатура блока кода <%s>' % code_block)
    return None


def exec_prev_post_decorate(func=None, prev_cmd=None, post_cmd=None, *args, **kwargs):
    """
    Выполнение внешней функции.
    Функция выполняется с пред... и пост... обработкой.
    @param func: Выполняемая функция.
    @param args: Аргументы выполняемой функции.
    @param kwargs: Аргументы выполняемой функции.
    @param prev_cmd: Блок кода пред обработки.
    @param post_cmd: Блок кода пост обработки.
    @return: Результат выполнения функции или None в случае ошибки.
    """
    prev_result = True
    if prev_cmd:
        log.info(u'Выполнение блока кода пред-обработки <%s>' % prev_cmd)
        # Перед выполнение произвести замену из контекста
        prev_result = exec_code_block(prev_cmd)

    if prev_result:
        # По результату предобработки определяем вообще надо производить чтение или нет
        if func:
            try:
                result = func(*args, **kwargs)
            except:
                log.fatal(u'Ошибка выполнения функции %s' % str(func))
                result = None
        else:
            log.warning(u'Не определена функция выполнения')
            result = None
    else:
        log.warning(u'Результат предварительной обработки не позволяет выполнить функцию %s' % str(func))
        result = None

    if post_cmd:
        log.info(u'Выполнение блока кода пост-обработки <%s>' % post_cmd)
        # Просто выполняем блок кода
        exec_code_block(post_cmd)

    return result

