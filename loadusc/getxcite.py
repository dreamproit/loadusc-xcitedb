#!python3
# -*- coding: utf-8 -*-
'Get nodes from XCiteDB XML database'

import sys
try:
    import re2 as re
except:
    import re

import logging
import subprocess
import json
from io import StringIO
from datetime import datetime

try:
    from constants import XCITEDBPATH, XMLDBPATH, SEC_REGEX, FULL_SEC_REGEX, TOC_REGEX, IDENTIFIER_TYPE_REGEX, USC_REGEX, NAMED_LAW_REGEX, BILLNUMBER_REGEX
except:
    from loadusc.constants import XCITEDBPATH, XMLDBPATH, SEC_REGEX, FULL_SEC_REGEX, TOC_REGEX, IDENTIFIER_TYPE_REGEX, USC_REGEX, NAMED_LAW_REGEX, BILLNUMBER_REGEX

logging.basicConfig(filename='loadusc.log', filemode='w', level='INFO')
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))


def getIdentifier(identifier='', date=datetime.now()):
    """Returns a Dict containing an array of the node(s) corresponding to `identifier` at `dateString`.

    Args:
        identifier (:obj:`str`): a string representation of the node to query 
        date (:obj:`datetime.datetime`): A datetime object. This function converts it to  `mm/DD/YYYY` format to call XCiteDB. Defaults to `datetime.now()`.

    Returns:
        dict:  
        
        The data returned from queries to XCiteDB, in the form::

            {
                'success': True/False,
                'message': 'Return warning, error or info',
                'xmls': ['<xmlstring/>',...] 
            }
    """
    respDict = {}
    if not identifier:
        respDict['success'] = False
        respDict['message'] = 'Identifier not provided'
        return respDict

    if not date or not isinstance(date, datetime):
        respDict['success'] = False
        respDict['message'] = 'Date must be a string of the form mm/dd/yyyy'
        return respDict
    else:
        dateString = date.strftime('%m/%d/%Y')

    queryTerms = None
    identifier = identifier.replace('-', '–')
    identifier = re.sub(r'\/$', '', identifier)
    identifier = re.sub(r'^\/uslm', '', identifier)

    identifierSearch = re.search(IDENTIFIER_TYPE_REGEX, identifier)
    if not identifierSearch:
        respDict['success'] = False
        respDict['message'] = 'Identifier not in the expected form'
        return respDict
    identifierType = identifierSearch.group(1)
    if (identifierType is None
            or (identifierType not in ['pl', 'usc', 'named'])):
        respDict['success'] = False
        respDict['message'] = 'Identifier must be of type pl, usc, or named'
        return respDict

    # Remove biglevels if there is a section specified in PL
    if identifierType == 'pl':
        identifier = identifier.replace(
            r'(\/us\/pl\/[0-9]+\/[0-9]+)\/(?:.*)(\/s[0-9].*$)', r'\1\2')

    if identifierType == 'named':
        namedSearch = re.search(NAMED_LAW_REGEX, identifier)
        if (namedSearch.group(2)):
            queryTerms = [
                '-match-start',
                namedSearch.group(1), '-match-end',
                namedSearch.group(2)
            ]
        else:
            pass

    # Remove biglevels if there is a section specified in USC
    if identifierType == 'usc':
        if not re.search(r'\/s[0-9]', identifier):
            uscSearch = re.search(USC_REGEX, identifier)
            if (uscSearch.group(2)):
                queryTerms = [
                    '-match-start',
                    uscSearch.group(1), '-match-end',
                    uscSearch.group(2)
                ]
        else:
            identifier = re.sub(
                r'(\/us\/usc\/t[0-9][^\/]*)\/(?:.*)(\/s[0-9].*$)', r'\1\2',
                identifier)

    if queryTerms is None:
        queryTerms = ['-match', identifier]

    queryList = [XCITEDBPATH, '-db', XMLDBPATH]
    if dateString:
        queryList.extend(['-date', dateString])

    queryTerms.insert(0, 'query')

    queryList.extend(queryTerms)
    dbquery = subprocess.run(queryList, timeout=60, capture_output=True)
    response = dbquery.stdout
    responseErr = dbquery.stderr
    if responseErr and len(responseErr) > 0:
        respDict['message'] = responseErr
        logger.info(responseErr)
    if response:
        logger.debug(response)
        respDict['xmls'] = json.loads(response)
        respDict['success'] = True
    else:
        respDict['success'] = False
    return respDict


def getChangeDates(identifier='', fromDate=None, toDate=None):
    """Returns a list of the dates of change corresponding to `identifier` between `fromDate` and `toDate`. 
    
    Currently only supports PL or USC identifiers; named law identifiers may have a '-match-end' query which is incompatible with a full log. 

    Args:
        identifier (:obj:`str`): a string representation of the node to query 
        fromDate (:obj:`datetime.datetime`): A datetime object. This function converts it to  `mm/DD/YYYY` format to call XCiteDB. Defaults to None.
        toDate (:obj:`datetime.datetime`): A datetime object. This function converts it to  `mm/DD/YYYY` format to call XCiteDB. Defaults to None.

    Returns:
        list of Dicts (from XCiteDB log) of the form:
            [
                {
                    "identifier": "/us/usc/t26/s25C/nt",
                    "date": "07/06/2016",
                    "action": "modified"
                },
                {
                    "identifier": "/us/usc/t26/s25C/nt",
                    "date": "02/26/2018",
                    "action": "modified"
                },
            ]
    """
    respDict = {}
    responseList = None
    responseMatchList = None
    try:
        fromDateString = fromDate.strftime('%m/%d/%Y')
        toDateString = toDate.strftime('%m/%d/%Y')
    except:
        fromDateString = None
        toDateString = None
    queryTerms = None
    identifier = identifier.replace('-', '–')
    identifier = re.sub(r'\/$', '', identifier)
    identifier = re.sub(r'^\/uslm', '', identifier)

    identifierSearch = re.search(IDENTIFIER_TYPE_REGEX, identifier)
    if not identifierSearch:
        respDict['success'] = False
        respDict['message'] = 'Identifier not in the expected form'
        return respDict
    identifierType = identifierSearch.group(1)
    if (identifierType is None or (identifierType not in ['usc'])):
        respDict['success'] = False
        respDict['message'] = 'Identifier must be of type pl or usc'
        return respDict

    # Remove biglevels if there is a section specified in PL
    if identifierType == 'pl':
        identifier = identifier.replace(
            r'(\/us\/pl\/[0-9]+\/[0-9]+)\/(?:.*)(\/s[0-9].*$)', r'\1\2')

    # Return if there is no section specified in USC
    if identifierType == 'usc':
        if not re.search(r'\/s[0-9]', identifier):
            respDict['success'] = False
            respDict[
                'message'] = 'US Code identifier must include a section for changeDates query'
            return respDict
        else:
            identifier = re.sub(
                r'(\/us\/usc\/t[0-9][^\/]*)\/(?:.*)(\/s[0-9].*$)', r'\1\2',
                identifier)
            identifier = identifier.rstrip('/') + '/'

    queryTermsMatch = ['-match', identifier.rstrip('/')]
    queryTerms = ['-match-start', identifier]

    queryList = [XCITEDBPATH, '-db', XMLDBPATH]
    if fromDateString and toDateString:
        queryList.extend(
            ['-from-date', fromDateString, '-to-date', toDateString])

    queryTerms.insert(0, 'query')
    queryTermsMatch.insert(0, 'query')

    queryListMatch = queryList.copy()
    queryList.extend(queryTerms)
    queryList.append('-log')
    logger.info(str(queryList))
    dbquery = subprocess.run(queryList, timeout=60, capture_output=True)
    response = dbquery.stdout
    responseErr = dbquery.stderr
    if responseErr and len(responseErr) > 0:
        respDict['message'] = responseErr
        logger.info(responseErr)
    if response:
        logger.debug(response)
        responseList = json.loads(response)
        logger.info(responseList)
    queryListMatch.extend(queryTermsMatch)
    queryListMatch.append('-log')
    logger.info(str(queryListMatch))
    dbqueryMatch = subprocess.run(queryListMatch,
                                  timeout=60,
                                  capture_output=True)
    responseMatch = dbqueryMatch.stdout
    responseMatchErr = dbqueryMatch.stderr
    if responseMatchErr and len(responseMatchErr) > 0:
        if respDict.get('message'):
            respDict['message'] = respDict['message'] + '; ' + responseMatchErr
        else:
            respDict['message'] = responseMatchErr

        logger.info(responseMatchErr)
    if responseMatch:
        logger.debug(responseMatch)
        responseMatchList = json.loads(responseMatch)
        if responseList:
            responseList.extend(responseMatchList)
            logger.debug(responseList)
            return responseList
        else:
            return responseMatchList
    else:
        if responseList:
            logger.debug(responseList)
            return responseList
        else:
            return []