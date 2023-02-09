#!python3
# -*- coding: utf-8 -*-

import os
import enum
from datetime import date

try:
    import re2 as re
except ImportError:
    import re

today = date.today()
TODAY_DD_MM_YYYY = today.strftime("%d/%m/%Y")
DATE_REGEX = r'[1-3]?[0-9]\/[1-3]?[0-9]\/[1-2][0-9]{3}'
DATE_REGEX_COMPILED = re.compile(DATE_REGEX)

# in Linux-like systems the environment variables can be set for all users in /etc/profile:
# export MAIN_ROOT_PATH='/main'
# export XMLDBPATH='/main/data_versions/xmldb'


class LOADUSC_XCiteDBConstants(enum.Enum):
    """Constants for loadusc-xcitedb."""

    ENV_NAME = 'dev_docker'


# Root path for XCiteDB
MAIN_ROOT_PATH = os.environ.get('MAIN_ROOT_PATH')
LOADUSC_XCiteDB_ENV_NAME = os.getenv('LOADUSC_XCiteDB_ENV_NAME', 'dev_local')
XCITEDBPATH = (
    os.path.join(
        os.getenv('XCITEDB_TOOL_PATH', '/var/XCiteDB/XCiteDB/bin/Release/XCiteDB')
    )
    if LOADUSC_XCiteDB_ENV_NAME == LOADUSC_XCiteDBConstants.ENV_NAME.value
    else os.path.abspath(
        os.path.join(MAIN_ROOT_PATH, 'XCiteDB', 'XCiteDB', 'bin', 'Release', 'XCiteDB')
    )
)

XMLDBPATH = os.getenv('XMLDBPATH', '/xml_dbs/xmldb')

DATA_PATH = (
    os.path.join(os.getenv('DATA_PATH', '/public/loadusc/data'))
    if LOADUSC_XCiteDB_ENV_NAME == LOADUSC_XCiteDBConstants.ENV_NAME.value
    else os.path.join(MAIN_ROOT_PATH, 'loadusc', 'data')
)
if not os.path.isdir(DATA_PATH):
    raise Exception('The data directory not found at:' + DATA_PATH + '.')

DOCCONFIGPATH = (
    os.path.abspath(
        os.path.join(
            MAIN_ROOT_PATH, 'House-Amendment-Parse', 'natparser', 'src', 'document.conf'
        )
    )
    if LOADUSC_XCiteDB_ENV_NAME == LOADUSC_XCiteDBConstants.ENV_NAME.value
    else os.path.abspath(os.path.join(DATA_PATH, 'document.conf'))
)

META_JSON_PATH = os.path.join(DATA_PATH, 'billmeta.json')
PUBLAWS_DICT_JSON_PATH = os.path.join(DATA_PATH, 'publawsDict.json')

USC_RELEASEPOINT_DIRPATH = (
    os.path.abspath(
        os.path.join(
            DATA_PATH,
            'USC_RELEASEPOINTS',
        )
    )
    if LOADUSC_XCiteDB_ENV_NAME == LOADUSC_XCiteDBConstants.ENV_NAME.value
    else os.path.abspath(os.path.join(MAIN_ROOT_PATH, 'USC_RELEASEPOINTS'))
)
USC_RELEASEPOINT_JSON_PATH = os.path.join(
    USC_RELEASEPOINT_DIRPATH, 'uscreleasepoints.json'
)

USC_HTML_PAGE_BASE = 'https://uscode.house.gov/download/'
CURRENT_USC_HTML_PAGE = "download.shtml"
USC_HTML_PAGE = 'priorreleasepoints.htm'
USC_RP_TEXT = 'usc-rp'
USC_XML_TEXT = 'xml_uscAll'

SEC_REGEX = r'^t.{1,4}\/s[^\/]+(:?\/nt)?'
FULL_SEC_REGEX = r'^.*\/s[0-9][^\/]*'
TOC_REGEX = r'^.*\/toc\/?'
IDENTIFIER_TYPE_REGEX = r'\/us\/([^\/]+)\/(.*)$'
USC_REGEX = r'(\/us\/usc\/t[^\/]+)(\/.*)?$'
USC_REGEX_COMPILED = re.compile(USC_REGEX)
NAMED_LAW_REGEX = r'(\/us\/named\/[^\/]+)(\/.*)?$'
USC_CITE_REGEX = r'([0-9]+[Aa]?)\s?[Uu]\.?[Ss]\.?[Cc]\.?\s?(?:([0-9]+[A-Za-z-]*)((?:\([a-z0-9]+\))*))'
USC_CITE_REGEX_COMPILED = re.compile(USC_CITE_REGEX)

BILLNUMBER_REGEX = r'^([0-9]{3})([a-z]+)([0-9]{1,4})([a-z]+)?$'
