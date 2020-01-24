#!python3
# -*- coding: utf-8 -*-
'Utils for processing Publaw and USC data'

import datetime
from bson import json_util
from loadusc.constants import META_JSON_PATH, PUBLAWS_DICT_JSON_PATH

def convertDTToDate(datetimeItem):
    return datetime.datetime.strftime(datetimeItem, '%m-%d-%Y')

# Publaw query:
#mongodb/uscongress/bill_info?filter={olrc_publaw:{$exists:1}}&keys={publaw:1,publawNumber:1,publawDate:1,billCongressTypeNumber:1}
# use convertDTToDate to get a datestring

# Convert from array of publaws to dict
def plArrayToDict(publaws):
   return {pl.get('publaw'):pl for pl in publaws}

def savePublawDict():
    with open(META_JSON_PATH, 'r') as f:
        metaDict = json_util.loads(f.read())
    plDict = plArrayToDict(metaDict.get('publaws'))
    with open(PUBLAWS_DICT_JSON_PATH,'w') as f_pl:
        f_pl.write(json_util.dumps(plDict))

    