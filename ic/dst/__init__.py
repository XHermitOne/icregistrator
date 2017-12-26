#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Пакет классов-получателей данных.
Кроме описания класса он д.б. зарегистрирован в словаре получателей данных.
"""

from . import txt_fmt
from . import sql_query
from . import cmd_list

DATA_DESTINATIONS = {
    'TXT_FMT': txt_fmt.icTxtFmtDataDestination,
    'SQL_DST': sql_query.icSQLQueryDataDestination,
    'CMD_LIST': cmd_list.icCmdListDataDestination,
}
