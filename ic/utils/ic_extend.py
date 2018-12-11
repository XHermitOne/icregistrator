#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Дополниетельные сервисные функции.
"""

# --- Imports ---
import sys
import sysconfig
import os
import os.path
import pwd
import stat
import getpass
import shutil
import traceback
import struct

try:
    from . import ic_str
except:
    print(u'Import error ic_str module')

__version__ = (0, 0, 1, 2)


DEFAULT_ENCODING = 'utf-8'


def who_am_i():
    """
    Имя залогиненного пользователя.
    """
    return getpass.getuser()


def is_root_user():
    """
    Проверить текущий пользователь - root?
    @return: Функция возвращает True/False.
    """
    return bool(who_am_i().lower() == 'root')


def check_python_library_version(LibName_, LibVer_, Compare_='=='):
    """
    Проверка установлена ли библиотека указанной версии.
    @param LibName_: Имя библиотеки, например 'wx'.
    @param LibVer_: Версия библиотеки, например '2.8.8.1'.
    @param Compare_: Оператор сравнения.
    @return: Возвращает True/False.
    """
    import_cmd = 'import '+str(LibName_)
    try:
        exec(import_cmd)
        import_lib = eval(LibName_)
    except ImportError:
        # Нет такой библиотеки
        print(u'Check Library Error:', LibName_)
        return False

    if Compare_ == '==':
        # Проверка на сравнение
        print('Python Library:', LibName_, 'Version:', import_lib.__version__)
        return bool(import_lib.__version__ == LibVer_)
    elif Compare_ in ('>=', '=>'):
        # Проверка на больше или равно
        print('Python Library:', LibName_, 'Version:', import_lib.__version__)
        return version_compare_greate_equal(import_lib.__version__, LibVer_)
    else:
        print('Not supported compare:', Compare_)
    return False


def version_compare_greate_equal(Version1_, Version2_, Delimiter_='.'):
    """
    Сравнение версий на Version1_>=Version2_.
    @param Version1_: Версия 1. В строковом виде. Например '2.8.9.2'.
    @param Version2_: Версия 2. В строковом виде. Например '2.8.10.1'.
    @param Delimiter_: Разделитель. Например точка.
    """
    ver1 = tuple([int(sub_ver) for sub_ver in Version1_.split(Delimiter_)])
    ver2 = tuple([int(sub_ver) for sub_ver in Version2_.split(Delimiter_)])
    len_ver2 = len(ver2)
    for i, sub_ver1 in enumerate(ver1):
        if i >= len_ver2:
            return True
        sub_ver2 = ver2[i]
        if sub_ver1 < sub_ver2:
            return False
        elif sub_ver1 > sub_ver2:
            return True
    return True


def check_python_labraries(**kwargs):
    """
    Проверка установленных библиотек Python.
    """
    result = True
    for lib_name, lib_ver in kwargs.items():
        result = result and check_python_library_version(lib_name, lib_ver)
    return result


def check_linux_package(PackageName_, Version_=None, Compare_='=='):
    """
    Проверка установленного пакета Linux.
    @param PackageName_: Имя пакета, например 'libgnomeprintui'
    @param Version_: Версия пакета. Если None, то версия не проверяется.\
    @param Compare_: Метод проверки версии.
    @return: True-пакет установлен, False-не установлен, 
        None-система пакетов не определена.
    """
    if is_deb_linux():
        print('This Linux is Debian')
        return check_deb_linux_package(PackageName_, Version_, Compare_)
    else:
        print('This linux is not Debian')
    return None


def check_deb_linux_package(PackageName_, Version_=None, Compare_='=='):
    """
    Проверка установленного пакета Linux.
    @param PackageName_: Имя пакета, например 'libgnomeprintui'
    @param Version_: Версия пакета. Если None, то версия не проверяется.\
    @param Compare_: Метод проверки версии.
    @return: True-пакет установлен, False-не установлен, 
        None-система пакетов не определена.
    """
    cmd = None
    try:
        cmd = 'dpkg-query --list | grep \'ii \' | grep \'%s\'' % PackageName_
        result = os.popen3(cmd)[1].readlines()
        return bool(result)
    except:
        print('Check Debian installed package Error', cmd)
        raise
    return None    


def check_deb_package_install(sPackageName):
    """
    Проверка установленн ли пакет DEB.
    @param sPackageName: Имя пакета, например 'libgnomeprintui'
    @return: True-пакет установлен, False-не установлен, 
        None-система пакетов не определена.
    """
    return check_deb_linux_package(sPackageName)


def get_uname(Option_='-a'):
    """
    Результат выполнения комманды uname.
    """
    cmd = None
    try:
        cmd = 'uname %s' % Option_
        return os.popen3(cmd)[1].readline()
    except:
        print('Uname Error', cmd)
        raise
    return None    


def get_linux_name():
    """
    Определить название Linux операционной системы и версии.
    """
    try:
        if os.path.exists('/etc/issue'):
            # Обычно Debian/Ubuntu Linux
            cmd = 'cat /etc/issue'
            return os.popen3(cmd)[1].readline().replace('\\n', '').replace('\\l', '').strip()
        elif os.path.exists('/etc/release'):
            # Обычно RedHat Linux
            cmd = 'cat /etc/release'
            return os.popen3(cmd)[1].readline().replace('\\n', '').replace('\\l', '').strip()
    except:
        print('Get linux name ERROR')
        raise
    return None


DEBIAN_LINUX_NAMES = ('Ubuntu', 'Debian', 'Mint', 'Knopix')


def is_deb_linux():
    """
    Проверка является ли дистрибутив c системой пакетов Debian.
    @return: Возвращает True/False.
    """
    linux_name = get_linux_name()
    print('Linux name:', linux_name)
    return bool([name for name in DEBIAN_LINUX_NAMES if name in linux_name])


def is_deb_linux_uname():
    """
    Проверка является ли дистрибутив c системой пакетов Debian.
    Проверка осуществляется с помощью команды uname.
    ВНИМАНИЕ! Это не надежный способ.
    Функция переписана.
    @return: Возвращает True/False.
    """
    uname_result = get_uname()
    return ('Ubuntu' in uname_result) or ('Debian' in uname_result)


def get_dist_packages_path():
    """
    Путь к папке 'dist-packages' или 'site_packages' 
    (в зависимости от дистрибутива) Python.
    """
    python_stdlib_path = sysconfig.get_path('stdlib')
    site_packages_path = os.path.normpath(os.path.join(python_stdlib_path, 'site-packages'))
    dist_packages_path = os.path.normpath(os.path.join(python_stdlib_path, 'dist-packages'))
    if os.path.exists(site_packages_path):
        return site_packages_path
    elif os.path.exists(dist_packages_path):
        return dist_packages_path
    return None


def create_pth_file(PthFileName_, Path_):
    """
    Создание *.pth файла в папке site_packages.
    @param PthFileName_: Не полное имя pth файла, например 'ic.pth'.
    @param Path_: Путь который указывается в pth файле.
    @return: Возвращает результат выполнения операции True/False.
    """
    pth_file = None
    try:
        dist_packages_path = get_dist_packages_path()
        pth_file_name = os.path.join(dist_packages_path, PthFileName_)
        pth_file = open(pth_file_name, 'wt')
        pth_file.write(Path_)
        pth_file.close()
        pth_file = None
        
        # Установить права на PTH файл
        try:
            os.chmod(pth_file_name, stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)
        except:
            print(u'ERROR! Chmod function in create_pth_file')
        print('Create PTH file:', pth_file_name, 'path:', Path_)
        return True
    except:
        if pth_file:
            pth_file.close()
            pth_file = None
        raise
    return False


def unzip_to_dir(ZipFileName_, Dir_, bOverwrite=True, bConsole=False):
    """
    Распаковать *.zip архив в папку.
    @param ZipFileName_: Полное имя *.zip архива.
    @param Dir_: Указание папки, в которую будет архив разворачиваться.
    @param bOverwrite: Перезаписать существующие файлы без запроса?
    @param bConsole: Вывод в консоль?
    @return: Возвращает результат выполнения операции True/False.
    """
    try:
        overwrite = ''
        if bOverwrite:
            overwrite = '-o'
        unzip_cmd = 'unzip %s %s -d %s' % (overwrite, ZipFileName_, Dir_)
        if bConsole:
            os.system(unzip_cmd)
            return None
        else:
            return os.popen3(unzip_cmd)
    except:
        print('Unzip Error', unzip_cmd)
        raise
    return None


def targz_extract_to_dir(TarFileName_, Dir_, bConsole=False):
    """
    Распаковать *.tar архив в папку.
    @param TarFileName_: Полное имя *.tar архива.
    @param Dir_: Указание папки, в которую будет архив разворачиваться.
    @param bConsole: Вывод в консоль?
    @return: Возвращает результат выполнения операции True/False.
    """
    tar_extract_cmd = None
    try:
        tar_extract_cmd = 'tar --extract --verbose --directory=%s --file=%s' % (Dir_, TarFileName_)
        print('Tar extract command:', tar_extract_cmd, os.path.exists(TarFileName_))
        if bConsole:
            os.system(tar_extract_cmd)
            return None
        else:
            return os.popen3(tar_extract_cmd)
    except:
        print('Tar Extract Error', tar_extract_cmd)
        raise
    return None


def deb_pkg_install(sDEBFileName):
    """
    Установить deb пакет.
    @param sDEBFileName: Полное имя *.deb пакета.
    @return: Возвращает результат выполнения операции True/False.
    """
    deb_install_cmd = None
    try:
        deb_install_cmd = 'dpkg --install %s' % sDEBFileName
        print('DEB package install command:', deb_install_cmd, os.path.exists(sDEBFileName))
        return os.popen3(deb_install_cmd)
    except:
        print('DEB package install Error', deb_install_cmd)
        raise
    return None


def deb_pkg_uninstall(sDEBPackageName):
    """
    Деинсталлировать DEB пакет.
    @param sDEBPackageName: Имя пакета. Например dosemu.
    @return: Возвращает результат выполнения операции True/False.
    """
    deb_uninstall_cmd = None
    try:
        if check_deb_package_install:
            deb_uninstall_cmd = 'dpkg --remove %s' % sDEBPackageName
            print('DEB package uninstall command:', deb_uninstall_cmd)
            return os.popen3(deb_uninstall_cmd)
        else:
            print('WARNING: Package %s not installed' % sDEBPackageName)
    except:
        print('DEB package uninstall Error', deb_uninstall_cmd)
        raise
    return None


def get_home_path(UserName_=None):
    """
    Определить домашнюю папку.
    """
    if sys.platform[:3].lower() == 'win':
        home = os.environ['HOMEDRIVE']+os.environ['HOMEPATH']
        home = home.replace('\\', '/')
    else:
        if UserName_ is None:
            home = os.environ['HOME']
        else:
            user_struct = pwd.getpwnam(UserName_)
            home = user_struct.pw_dir
    return home


def get_login():
    """
    Имя залогинненного пользователя.
    """
    username = 'unknown'
    if 'USERNAME' in os.environ:
        username = os.environ['USERNAME']
    elif 'USER' in os.environ:
        username = os.environ['USER']
    elif 'LOGNAME' in os.environ:
        username = os.environ['LOGNAME']

    if username != 'root':
        return username
    else:
        return os.environ['SUDO_USER']
        

def dir_dlg(Title_='', DefaultPath_=''):
    """
    Диалог выбора каталога.
    @param Title_: Заголовок диалогового окна.
    @param DefaultPath_: Путь по умолчанию.
    """
    import wx
    app = wx.GetApp()
    result = ''
    dlg = None
    
    if app:
        try:
            main_win = app.GetTopWindow()

            dlg = wx.DirDialog(main_win, Title_,
                               style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)

            # Установка пути по умолчанию
            if not DefaultPath_:
                DefaultPath_ = os.getcwd()
            dlg.SetPath(DefaultPath_)
            if dlg.ShowModal() == wx.ID_OK:
                result = dlg.GetPath()
            else:
                result = ''
        finally:
            if dlg:
                dlg.Destroy()
                dlg = None

    return result


def file_dlg(Title_='', Filter_='', DefaultPath_=''):
    """
    Открыть диалог выбора файла для открытия/записи.
    @param Title_: Заголовок диалогового окна.
    @param Filter_: Фильтр файлов.
    @param DefaultPath_: Путь по умолчанию.
    @return: Возвращает полное имя выбранного файла.
    """
    import wx
    app = wx.GetApp()
    result = ''
    dlg = None
    
    if app:
        try:
            main_win = app.GetTopWindow()

            wildcard = Filter_+'|All Files (*.*)|*.*'
            dlg = wx.FileDialog(main_win, Title_, '', '', wildcard, wx.FD_OPEN)
            if DefaultPath_:
                dlg.SetDirectory(normpath(DefaultPath_, get_login()))
            else:
                dlg.SetDirectory(os.getcwd())
        
            if dlg.ShowModal() == wx.ID_OK:
                result = dlg.GetPaths()[0]
            else:
                result = ''
            dlg.Destroy()
        finally:
            if dlg:
                dlg.Destroy()

    return result


def get_dosemu_dir(UserName_=None):
    """
    Определить папку установленного dosemu.
    """
    home = get_home_path(UserName_)
    dosemu_dir = os.path.join(home, '.dosemu')
    if os.path.exists(dosemu_dir):
        return dosemu_dir
    else:
        return dir_dlg(u'Не найдена папка dosemu')
        
    return None


def check_dir(Dir_):
    """
    Проверить папку, если ее нет то она создается.
    """
    norm_dir = normpath(Dir_, get_login())
    if not os.path.exists(norm_dir):
        try:
            os.makedirs(norm_dir)
            return True
        except:
            print('ERROR! Make directory', norm_dir)
            return False
    else:
        return True


def save_file_text(FileName_, Txt_=''):
    """
    Запись текста в файл.
    @param FileName_; Имя файла.
    @param Txt_: Записываемый текст.
    @return: True/False
    """
    # if isinstance(Txt_, str):
    #    # Если передается текст в юникоде,
    #    #  то автоматом перекодировать в UTF-8
    #    Txt_ = Txt_.encode(DEFAULT_ENCODING)

    file_obj = None
    try:
        file_obj = open(FileName_, 'wt')
        file_obj.write(Txt_)
        file_obj.close()
        return True
    except:
        if file_obj:
            file_obj.close()
        print('Save text file', FileName_, 'ERROR')
        print(traceback.format_exc())
    return False


def load_file_text(FileName_, code_page='utf-8',
                   to_unicode=False):
    """
    Чтение текстового файла.
    @param FileName_; Имя файла.
    @param code_page: Кодовая страница файла
        (для преобразования в Unicode).
    @paran to_unicode: Преобразовать сразу в Unicode?
    @return: Текст файла.
    """
    if not os.path.exists(FileName_):
        print(u'File <%s> not found' % FileName_)
        return ''

    f = None
    try:
        f = open(FileName_, 'rt')
        txt = f.read()
        f.close()
    except:
        if f:
            f.close()
        print(u'Load text file <%s>' % FileName_)
        return ''

    # if to_unicode:
    #    return unicode(txt, code_page)
    return txt


def load_file_unicode(FileName_, code_page=None):
    """
    Чтение текстового файла сразу в виде unocode.
    Определение содовой страницы происходит автоматически.
    @param FileName_; Имя файла.
    @param code_page: Кодовая страница файла.
        Если не определена, то пробуем определить ее.
    @return: Текст файла в unicode.
    """
    body_text = load_file_text(FileName_)
    if not code_page:
        code_page = ic_str.get_codepage(body_text)
    return str(body_text)   # , code_page)


def recode_text_file(txt_filename, new_filename=None, src_codepage=None, dst_codepage='utf-8'):
    """
    Перекодировать текстовый файл из одной кодирровки в другую.
    @param txt_filename: Полное наименование текстового файла.
    @param new_filename: Полное наименование результирующего текстового файла.
        Если не определено, то берется исходное имя файла.
    @param src_codepage: Исходная кодировка.
        Если None, то пробуем определить исходную кодировку файла.
    @param dst_codepage: Результирующая кодировка.
        По умолчанию utf-8.
    @return: True - удачно перекодировали. False - ошибка.
    """
    if not os.path.exists(txt_filename):
        print(u'Файл <%s> не найден' % txt_filename)
        return False

    if not new_filename:
        new_filename = txt_filename

    txt_unicode = load_file_unicode(txt_filename, src_codepage)

    if txt_unicode and isinstance(txt_unicode, str):
        txt_str = txt_unicode   # .encode(dst_codepage)
        if os.path.exists(new_filename):
            try:
                os.remove(new_filename)
            except:
                print(u'Ошибка удаления файла <%s>' % new_filename)
                return False
        return save_file_text(new_filename, txt_str)
    return False


def copy_file_to(SrcFileName_, DstPath_, ReWrite_=True):
    """
    Копировать файл в указанную папку.
    @param SrcFileName_: Имя файла-источника.
    @param DstPath_: Папка-назначение.
    @param ReWrite_: Перезаписать файл, если он уже существует?
    """
    try:
        DstPath_ = normpath(DstPath_, get_login())
        if not os.path.exists(DstPath_):
            os.makedirs(DstPath_)
        dst_file_name = os.path.join(DstPath_, os.path.basename(SrcFileName_))
        if ReWrite_:
            if os.path.exists(dst_file_name):
                os.remove(dst_file_name)
        shutil.copyfile(SrcFileName_, dst_file_name)
        return True
    except:
        return False


def set_chown_login(sPath):
    """
    Установить владельца файла/папки залогиненного пользователя.
    """
    if not os.path.exists(sPath):
        return False
    username = get_login()
    user_struct = pwd.getpwnam(username)
    uid = user_struct.pw_uid
    gid = user_struct.pw_gid
    path = normpath(sPath, username)
    return os.chown(path, uid, gid)


def set_public_chmod(sPath):
    """
    Установить свободный режим доступа (0x777) к файлу/папке.
    """
    path = normpath(sPath, get_login())
    if os.path.exists(path):
        return os.chmod(path, stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)
    return False


def set_public_chmode_tree(sPath):
    """
    Установить свободный режим доступа (0x777) к файлу/папке рекурсивно.
    """
    path = normpath(sPath, get_login())
    result = set_public_chmod(path)
    if os.path.isdir(path):
        for f in os.listdir(path):
            pathname = os.path.join(path, f)
            set_public_chmode_tree(pathname)
    return result


def sym_link(sLinkPath, sLinkName, sUserName=None, bOverwrite=True):
    """
    Создать символическую ссылку.
    @param sLinkPath: На что ссылается ссылка.
    @param sLinkName: Имя ссылки.
    @param sUserName: Имя пользователя.
    @param bOverwrite: Перезаписать ссылку, если она существует?
    """ 
    username = sUserName
    if username is None:
        username = get_login()
    link_path = normpath(sLinkPath, username)
    link_name = normpath(sLinkName, username)
    
    if os.path.exists(link_name) and bOverwrite:
        # Перезаписать?
        os.remove(link_name)
    try:
        return os.symlink(link_path, link_name)
    except:
        print('ERROR! Create symbolic link:', link_name, '->', link_path)
        raise
    return None


def get_options(lArgs=None):
    """
    Преобразование параметров коммандной строки в словарь python.
    Параметры коммандной строки в виде --ключ=значение.
    @param lArgs: Список строк параметров.
    @return: Словарь значений или None в случае ошибки.
    """
    if lArgs is None:
        lArgs = sys.argv[1:]
        
    opts = {}
    args = []
    while lArgs:
        if lArgs[0][:2] == '--':
            if '=' in lArgs[0]:
                # поиск пар “--name=value”
                i = lArgs[0].index('=')
                # ключами словарей будут имена параметров
                opts[lArgs[0][:i]] = lArgs[0][i+1:]
            else:
                # поиск “--name”
                # ключами словарей будут имена параметров
                opts[lArgs[0]] = True
        else:
            args.append(lArgs[0])
        lArgs = lArgs[1:]
    return opts, args
    
    
def normpath(path, sUserName=None):
    """
    Нормировать путь.
    @param path: Путь.
    @param sUserName: Имя пользователя.
    """
    home_dir = get_home_path(sUserName)
    return os.path.abspath(os.path.normpath(path.replace('~', home_dir)))


def isLinuxPlatform():
    """
    ОС linux?
    """
    return sys.platform.lower().startswith('lin')


def isWindowsPlatform():
    """
    ОС windows?
    """
    return sys.platform.lower().startswith('win')


def getPlatform():
    """
    ОС
    """
    return sys.platform


def copyFile(sFileName, sNewFileName, bRewrite=True):
    """
    Создает копию файла с новым именем.
    @type sFileName: C{string}
    @param sFileName: Полное имя файла.
    @type sNewFileName: C{string}
    @param sNewFileName: Новое имя файла.
    @type bRewrite: C{bool}
    @param bRewrite: True-если новый файл уже существует,
        то переписать его молча. False-если новый файл уже существует,
        то не перезаписывать его а оставить старый.
    @return: Возвращает результат выполнения операции True/False.
    """
    try:
        # Проверка существования файла-источника
        if not os.path.isfile(sFileName):
            print('WARNING! File %s not exist for copy' % sFileName)
            return False

        # Проверка перезаписи уже существуещего файла
        if not bRewrite:
            print('WARNING! File %s exist and not rewrite' % sFileName)
            return False

        # Создать результирующую папку
        dir = os.path.dirname(sNewFileName)
        if not os.path.exists(dir):
            os.makedirs(dir)
        shutil.copyfile(sFileName, sNewFileName)
        return True
    except IOError:
        print('ERROR! Copy file %s I/O error' % sFileName)
        return False


def copyToDir(sFileName, sDestDir, bRewrite=True):
    """
    Копировать файл в папку.
    @type sFileName: C{string}
    @param sFileName: Имя файла.
    @type sDestDir: C{string}
    @param sDestDir: Папка в которую необходимо скопировать.
    @type bRewrite: C{bool}
    @param bRewrite: True-если новый файл уже существует,
        то переписать его молча. False-если новый файл уже существует,
        то не перезаписывать его а оставить старый.
    @return: Возвращает результат выполнения операции True/False.
    """
    return copyFile(sFileName, os.path.join(sDestDir, os.path.basename(sFileName)), bRewrite)


def changeExt(sFileName, sNewExt):
    """
    Поменять у файла расширение.
    @type sFileName: C{string}
    @param sFileName_: Полное имя файла.
    @type sNewExt: C{string}
    @param sNewExt: Новое расширение файла (Например: '.bak').
    @return: Возвращает новое полное имя файла.
    """
    try:
        new_name = os.path.splitext(sFileName)[0]+sNewExt
        if os.path.isfile(new_name):
            os.remove(new_name)     # если файл существует, то удалить
        if os.path.exists(sFileName):
            os.rename(sFileName, new_name)
            return new_name
    except:
        print('ERROR! Cange ext file %s' % sFileName)
        raise
    return None


def parseCmd(sCommand):
    """
    Распарсить комманду.
    @type sCommand: c{string}
    @param sCommand: Строковое представление комманды.
    @return: Список [<Комманда>,<Аргумент1>,<Аргумент2>,..]
    """
    parse_args = sCommand.strip().split(' ')
    args = []
    i = 0
    while i < len(parse_args):
        parse_arg = parse_args[i]
        if parse_arg[0] == '"' and parse_arg[-1] != '"':
            while parse_arg[-1] != '"' and i < len(parse_args):
                i += 1
                parse_arg += ' '+parse_args[i]
        # Стереть """
        if parse_arg[0] == '"':
            parse_arg = parse_arg[1:]
        if parse_arg[-1] == '"':
            parse_arg = parse_arg[:-1]

        args.append(parse_arg)
        i += 1
    return args


def getComputerName():
    """
    Имя компютера. Без перекодировки.
    @return: Получить имя компьютера в сети.
        Имя компьютера возвращается в utf-8 кодировке.
    """
    import socket
    comp_name = socket.gethostname()
    if isWindowsPlatform():
        # Если win то поменять кодировку c cp1251 на utf-8
        comp_name = str(comp_name)  # , 'cp1251').encode('utf-8')
    return comp_name


def getComputerNameLAT():
    """
    Имя компютера. Все русские буквы заменяются латиницей.
    @return: Получить имя компьютера в сети.
    """
    comp_name = None
    if 'COMPUTERNAME' in os.environ:
        comp_name = os.environ['COMPUTERNAME']
    else:
        import socket
        comp_name = socket.gethostname()

    # ВНИМАНИЕ! Имена компьютеров должны задаваться только латиницей
    # Под Win32 можно задать имя компа русскими буквами и тогда
    # приходится заменять все на латиницу.
    if isinstance(comp_name, str):
        if isWindowsPlatform():
            comp_name = str(comp_name)  # , 'cp1251')
            comp_name = rus2lat(comp_name)
    return comp_name


def _rus2lat(sText, dTranslateDict):
    """
    Перевод русских букв в латинские по словарю замен.
    @param sText: Русский текст.
    @param dTranslateDict: Словарь замен.
    """
    # if not isinstance(sText, unicode):
    #    # Привести к юникоду
    #    sText = unicode(sText, 'utf-8')

    txt_list = list(sText)
    txt_list = [dTranslateDict.setdefault(ch, ch) for ch in txt_list]
    return ''.join(txt_list)


RUS2LATDict = {u'а': 'a', u'б': 'b', u'в': 'v', u'г': 'g', u'д': 'd', u'е': 'e', u'ё': 'yo', u'ж': 'j',
               u'з': 'z', u'и': 'i', u'й': 'y', u'к': 'k', u'л': 'l', u'м': 'm', u'н': 'n', u'о': 'o', u'п': 'p',
               u'р': 'r', u'с': 's', u'т': 't', u'у': 'u', u'ф': 'f', u'х': 'h', u'ц': 'c', u'ч': 'ch',
               u'ш': 'sh', u'щ': 'sch', u'ь': '', u'ы': 'y', u'ъ': '', u'э': 'e', u'ю': 'yu', u'я': 'ya',
               u'А': 'A', u'Б': 'B', u'В': 'V', u'Г': 'G', u'Д': 'D', u'Е': 'E', u'Ё': 'YO', u'Ж': 'J',
               u'З': 'Z', u'И': 'I', u'Й': 'Y', u'К': 'K', u'Л': 'L', u'М': 'M', u'Н': 'N', u'О': 'O', u'П': 'P',
               u'Р': 'R', u'С': 'S', u'Т': 'T', u'У': 'U', u'Ф': 'F', u'Х': 'H', u'Ц': 'C', u'Ч': 'CH',
               u'Ш': 'SH', u'Щ': 'SCH', u'Ь': '', u'Ы': 'Y', u'Ъ': '', u'Э': 'E', u'Ю': 'YU', u'Я': 'YA'}


def rus2lat(sText):
    """
    Перевод русских букв в латинские.
    """
    return _rus2lat(sText, RUS2LATDict)


def norm_path(sPath, sDelim=os.path.sep):
    """
    Удалить двойные разделител из пути.
    @type sPath: C{string}
    @param sPath: Путь
    @type sDelim: C{string}
    @param sDelim: Разделитель пути
    """
    sPath = sPath.replace('~', getHomeDir())
    dbl_delim = sDelim+sDelim
    while dbl_delim in sPath:
        sPath = sPath.replace(dbl_delim, sDelim)
    return sPath


def getHomeDir():
    """
    Папка HOME.
    @return: Строку-путь до папки пользователя.
    """
    if isWindowsPlatform():
        home_dir = os.environ['HOMEDRIVE']+os.environ['HOMEPATH']
        home_dir = home_dir.replace('\\', '/')
    else:
        home_dir = os.environ['HOME']
    return os.path.normpath(home_dir)


def text_file_append(sTextFileName, sText, CR='\n'):
    """
    Добавить строки в текстовый файл.
    Если файл не существует, то файл создается.
    @param sTextFileName: Имя текстового файла.
    @param sText: Добавляемый текст.
    @param CR: Символ возврата каретки.
    @return: True/False.
    """
    txt_filename = normpath(sTextFileName, get_login())
    txt = ''

    if os.path.exists(txt_filename):
        f = None
        try:
            f = open(txt_filename, 'rt')
            txt = f.read()
            txt += CR
            txt += sText
            print('Text file append <%s> in <%s>' % (sText, txt_filename))
            f.close()
        except:
            print('Text file append in <%s>' % txt_filename)
            if f:
                f.close()
                f = None
    else:
        txt = sText

    f = None
    try:
        f = open(txt_filename, 'wt')
        f.write(txt)
        f.close()
        f = None
        return True
    except:
        print('Text file append in <%s>' % txt_filename)
        if f:
            f.close()
            f = None
    return False


def text_file_replace(sTextFileName, sOld, sNew, bAutoAdd=True, CR='\n'):
    """
    Замена строки в текстовом файле.
    @param sTextFileName: Имя текстового файла.
    @param sOld: Старая строка.
    @param sNew: Новая строка.
    @param bAutoAdd: Признак автоматического добавления новой строки.
    @param CR: Символ возврата каретки.
    @return: True/False.
    """
    txt_filename = normpath(sTextFileName, get_login())
    if os.path.exists(txt_filename):
        f = None
        try:
            f = open(txt_filename, 'rt')
            txt = f.read()
            txt = txt.replace(sOld, sNew)
            if bAutoAdd and (sNew not in txt):
                txt += CR
                txt += sNew
                print('Text file append <%s> in <%s>' % (sNew, txt_filename))
            f.close()
            f = None
            f = open(txt_filename, 'wt')
            f.write(txt)
            f.close()
            f = None
            return True
        except:
            print('Text file replace in <%s>' % txt_filename)
            if f:
                f.close()
                f = None
    else:
        print('File <%s> not exists' % txt_filename)
    return False


def text_file_find(sTextFileName, sFind):
    """
    Поиск строки в текстовом файле.
    @param sTextFileName: Имя текстового файла.
    @param sFind: Сирока поиска.
    @return: True/False.
    """
    txt_filename = normpath(sTextFileName, get_login())
    if os.path.exists(txt_filename):
        f = None
        try:
            f = open(txt_filename, 'rt')
            txt = f.read()
            result = sFind in txt
            f.close()
            f = None
            return result
        except:
            print('Find <%s> in text file <%s>' % (sFind, txt_filename))
            if f:
                f.close()
                f = None
    else:
        print('File <%s> not exists' % txt_filename)
    return False


def text_file_subreplace(sTextFileName, sSubStr, sNew, bAutoAdd=True, CR='\n'):
    """
    Замена строки в текстовом файле с поиском подстроки.
    @param sTextFileName: Имя текстового файла.
    @param sSubStr: Под строка  выявления строки замены.
    @param sNew: Новая строка.
    @param bAutoAdd: Признак автоматического добавления новой строки.
    @param CR: Символ возврата каретки.
    @return: True/False.
    """
    txt_filename = normpath(sTextFileName, get_login())
    if os.path.exists(txt_filename):
        f = None
        try:
            f = open(txt_filename, 'rt')
            lines = f.readlines()
            is_replace = False
            for i, line in enumerate(lines):
                if sSubStr in line:
                    lines[i] = sNew
                    is_replace = True
                    print('Text file replace <%s> -> <%s> in <%s>' % (line, sNew, txt_filename))
            if bAutoAdd and not is_replace:
                lines += [CR]
                lines += [sNew]
                print('Text file append <%s> in <%s>' % (sNew, txt_filename))
            f.close()
            f = None
            f = open(txt_filename, 'wt')
            f.writelines(lines)
            f.close()
            f = None
            return True
        except:
            print('Text file sub replace in <%s>' % txt_filename)
            if f:
                f.close()
                f = None
    else:
        print('File <%s> not exists' % txt_filename)
    return False


def text_file_subdelete(sTextFileName, sSubStr):
    """
    Удаление строки в текстовом файле с поиском подстроки.
    @param sTextFileName: Имя текстового файла.
    @param sSubStr: Под строка  выявления строки удаления.
    @return: True/False.
    """
    txt_filename = normpath(sTextFileName, get_login())
    if os.path.exists(txt_filename):
        f = None
        try:
            result_lines = []
            f = open(txt_filename, 'rt')
            lines = f.readlines()
            for line in lines:
                if sSubStr not in line:
                    result_lines.append(line)
                else:
                    print('Text file delete line <%s> from <%s>' % (line, txt_filename))
            f.close()
            f = None
            f = open(txt_filename, 'wt')
            f.writelines(result_lines)
            f.close()
            f = None
            return True
        except:
            print('Text file sub delete in <%s>' % txt_filename)
            if f:
                f.close()
                f = None
    else:
        print('File <%s> not exists' % txt_filename)
    return False


def exec_sys_command(sCommand):
    """
    Функция выполнения команды ОС.
    @param sCommand: Текст команды.
    """
    try:
        os.system(sCommand)
        print('Execute command: %s' % sCommand)
    except:
        print('ERROR. Execute command: %s' % sCommand)
        raise


def targz_install_python_package(targz_package_filename=None):
    """
    Установить Python пакет в виде tar.gz архива.
    @param targz_package_filename: Имя файла архива поставки Python пакета.
    @return: True/False.
    """
    if not targz_package_filename:
        print('Not define TARGZ python package file.')
        return False

    if not os.path.exists(targz_package_filename):
        print('Not exists <%s> python package file.' % targz_package_filename)
        return False

    print('Start install python package. TarGz filename <%s>' % targz_package_filename)

    pkg_dir = os.path.dirname(targz_package_filename)
    set_public_chmod(pkg_dir)
    targz_extract_to_dir(targz_package_filename, pkg_dir)

    targz_basename = os.path.splitext(os.path.basename(targz_package_filename))[0]
    setup_dir = os.path.normpath(os.path.join(pkg_dir, targz_basename))
    setup_filename = os.path.normpath(os.path.join(setup_dir, 'setup.py'))
    if os.path.exists(setup_filename):
        cmd = 'cd %s; sudo %s setup.py install' % (setup_dir, sys.executable)
        print('Install <%s> library. Command <%s>' % (targz_basename, cmd))
        os.system(cmd)
        # Удалить после инсталляции распакованный архив
        if os.path.exists(setup_dir):
            cmd = 'sudo rm -R %s' % setup_dir
            print('Delete setup directory <%s>. Command <%s>' % (setup_dir, cmd))
            os.system(cmd)
        return True
    else:
        print('WARNING. Don\'t exist setup.py file <%s>' % setup_filename)
    return False


def checkPingHost(host_name):
    """
    Проверка связи с хостом по пингу (ping).
    @param host_name: Имя хоста.
    @return: True - связь с хостом есть. False - сбой связи.
    """
    response = os.system('ping -c 1 %s' % host_name)
    return response == 0


def loadBinaryFile(filename):
    """
    Загрузить данные бинарного файла.
    @param filename: Полное имя загружаемого файла.
    @return: Бинарные данные файла.
    """
    if os.path.exists(filename):
        data = open(filename, 'rb').read()
        return bytearray(data)
    else:
        print('WARNING. Don\'t exist file <%s>' % filename)
    return None


def is_float_str(txt):
    """
    Определить является ли строка числом с плавающей запятой.
    @param txt: Анализируемая строка.
    @return: True/False
    """
    try:
        float(txt)
        return True
    except ValueError:
        return False


def is_int_str(txt):
    """
    Определить является ли строка целым числом.
    @param txt: Анализируемая строка.
    @return: True/False
    """
    return txt.isdigit()


def is_None_str(txt):
    """
    Определить является ли строка None.
    @param txt: Анализируемая строка.
    @return: True/False
    """
    return txt.strip() == 'None'


def wise_type_translate_str(txt):
    """
    Преобразование типа из строки к реальному типу.
    @param txt: Анализируемая строка.
    @return: Значение строки реального типа.
        Например:
            txt = 'None' - Результат None
            txt = '099' - Результат 99
            txt = '3.14' - Результат 3.14
            txt = 'XYZ' - Результат 'XYZ'
    """
    if is_None_str(txt):
        return None
    elif is_int_str(txt):
        return int(txt)
    elif is_float_str(txt):
        return float(txt)
    # Не можем преобразовать в какой либо вид
    # Значит это строка
    return txt


def test():
    """
    Функция тестирования.
    """
    result = get_options(['--dosemu=/home/user/.dosemu', '--option2', 'aaaa'])
    print('TEST>>>', result)


if __name__ == '__main__':
    test()
