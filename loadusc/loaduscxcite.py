#!python3
# -*- coding: utf-8 -*-
'Load USC release points from local files into XCiteDB in chronological order'

import sys
import os
import argparse
import logging
import json
import subprocess
from bson import json_util
try:
    import re2 as re
except:
    import re
try:
    from constants import XCITEDBPATH, XMLDBPATH, DOCCONFIGPATH, USC_RELEASEPOINT_DIRPATH, USC_RELEASEPOINT_JSON_PATH, PUBLAWS_DICT_JSON_PATH
except:
    from loadusc.constants import XCITEDBPATH, XMLDBPATH, DOCCONFIGPATH, USC_RELEASEPOINT_DIRPATH, USC_RELEASEPOINT_JSON_PATH, PUBLAWS_DICT_JSON_PATH

logging.basicConfig(filename='loadusc.log', filemode='w', level='INFO')
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

    # ** To check if the version has been uploaded **
    # ** XCiteDB inspect -t log -match-start 20150501 **
    # ** Will give changes from that date or error if there are none **
    #    if release_date:
    #        release_date_parts = release_date.split('/')
    # version_date = release_date_parts[2] + release_date_parts[0] + release_date_parts[1]
    # dbquery = subprocess.run([XCITEDBPATH, 'inspect', '-t', 'log', '-match-start', version_date], timeout=20, capture_output=True)
    # response = dbquery.stdout
    # responseErr = dbquery.stderr

    # ** If no match, load to XCiteDB **
    # ** XCiteDB -dc document.conf -date <mm/dd/yyyy> load-xml -r <path to release point directory **
    # if responseErr is not None:
    #    dbload = subprocess.run([XCITEDBPATH, '-db', XMLDBPATH, '-dc', XE_DC_PATH, '-date', release_date, 'load-xml', -r, release_point_path] , timeout=20, capture_output=True)

def sortPLS(pl):
    pl.split('-')
    l=list(map(lambda x: int(x),pl.split('-'))) 
    return l[0]*10000+l[1]


def loadUSCReleasePointsFromJSON(releasepointJSONPath = USC_RELEASEPOINT_JSON_PATH, publawsDict=PUBLAWS_DICT_JSON_PATH):
    # releasepoints, from the releasepoint scraper is a list of releasepoints with the filename as 'name' and a list of 'titlesAffected' 
    with open(releasepointJSONPath, 'r') as f:
        releasepoints = json.load(f)
    releasepoints_rev = releasepoints[::-1]
    
    # pljson is a list of public laws and their enactment dates
    with open(publawsDict, 'r') as f:
        pljson = json_util.loads(f.read())
    
    pls = [item.get('name') for item in releasepoints_rev if not (re.search(r'not',item.get('name')) or re.search(r'u1$',item.get('name')))]
    plsDict = dict((item.get('name'), index) for index, item in enumerate(releasepoints_rev))
    print(plsDict)
    pls.sort(key=sortPLS)
    prior_index = 0
    for pl in pls:
        pljsonitem = pljson.get(pl) 
        if not pljsonitem:
            logger.error('No item for ' + str(pl))
            continue
        publaw_date = pljsonitem.get('publawDate')
        if publaw_date:
            release_date = publaw_date.strftime('%m/%d/%Y')
        # Get the list of names from the last pl until and including the current one
        plIndex=plsDict.get(pl)
        for rp in releasepoints_rev[prior_index:plIndex+1]:
            rpname = rp.get('name')
            release_point_path = os.path.join(USC_RELEASEPOINT_DIRPATH, rpname)
            logger.info(release_point_path)
            dbload = None
            try:
                logger.info('Loading release point ' + rpname + ' for date: ' + release_date)
                logger.info(str([XCITEDBPATH, '-db', XMLDBPATH, '-date', release_date, 'load-xml', '-r', release_point_path]))
                dbload = subprocess.run([XCITEDBPATH, '-db', XMLDBPATH, '-dc', DOCCONFIGPATH, '-date', release_date, 'load-xml', '-r', release_point_path] , timeout=600, capture_output=True)
            except Exception as err:
                logger.error('Could not load release point for ' + rpname)
                logger.error(err)
        prior_index = plIndex+1
        if dbload:
            logger.info(dbload.stdout)
            logger.info(dbload.stderr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Load USC releasepoints.', epilog='')
   # parser.add_argument(
   #     '-d',
   #     '--debug',
   #     action='store',
   #     dest='loglevel',
   #     default='ERROR',
   #     help='Set the debug level (default: %(default)s)')

    args = parser.parse_args()

    logger.info(json.dumps(args.__dict__))
    logger.info('===============================')

    loadUSCReleasePointsFromJSON(**args.__dict__)
