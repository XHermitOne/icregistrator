#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Пакет классов-источников данных.
Кроме описания класса он д.б. зарегистрирован в словаре источников данных.
"""

from . import rslinx
from . import uni_opc
from . import xml_file
from . import utm
from . import src_query
from . import file_list

DATA_SOURCES = {
    'RSLINX': rslinx.icRSLinxDataSource,
    'UNI_OPC': uni_opc.icUniReaderOPCDataSource,
    'XML_FILE': xml_file.icXMLFileDataSource,
    'UTM': utm.icUTMDataSource,
    'SQL_SRC': src_query.icSQLQueryDataSource,
    'FILE_LIST': file_list.icFileListDataSource,
}
