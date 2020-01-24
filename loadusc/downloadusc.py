#!python3
# -*- coding: utf-8 -*-
'Scrape USC release points'

# Sample release point link: https://uscode.house.gov/download/releasepoints/us/pl/115/239not232/usc-rp@115-239not232.htm

import zipfile
import re
import io
import sys
import os
from bs4 import BeautifulSoup
import requests
import subprocess
import logging
import json
import argparse

try:
    from constants import USC_RELEASEPOINT_DIRPATH, USC_RELEASEPOINT_JSON_PATH, USC_HTML_PAGE_BASE, USC_HTML_PAGE, CURRENT_USC_HTML_PAGE, USC_RP_TEXT, USC_XML_TEXT
except:
    from loadusc.constants import USC_RELEASEPOINT_DIRPATH, USC_RELEASEPOINT_JSON_PATH, USC_HTML_PAGE_BASE, USC_HTML_PAGE, CURRENT_USC_HTML_PAGE, USC_RP_TEXT, USC_XML_TEXT


URL_ATTEMPTS_MAX = 20

logging.basicConfig(filename='loadusc.log', filemode='w', level='INFO')
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))


def getAndUnzipURL(url: string, dir_name: str, titlesAffected: list=['All'], redownload: bool=False):
    """
    Given a url downlowd zip file for a U.S. Code title

    Args:
        url (string): url location for the .zip 
        dir_name (str): name of the directory to download 
        titlesAffected (list, optional): list of titles of the USC affected by the releasepoint. Defaults to ['All'].
        redownload (bool, optional): replace existind releasepoint, if it exists in local directory. Defaults to False.
    """
    print('Getting USC updates for: ' + url)
    if not os.path.exists(dir_name) or redownload:
        for title in titlesAffected:
            if title is not 'All':
                title = title.lower()
            if len(title.replace('a', '')) == 1:
                title = '0' + title
            print('Getting title: ' + title)
            url = re.sub(r"_usc.*@", "_usc" + title + "@", url)
            r = requests.get(url, stream=True)
            check = zipfile.is_zipfile(io.BytesIO(r.content))
            attempts = 0
            while not check:
                print('Trying to get url...')
                if(url.find('u1.zip')>0):
                    url2 = url.replace('u1.zip', '.zip')
                    r = requests.get(url2, stream=True)
                    check = zipfile.is_zipfile(io.BytesIO(r.content))
                if not check:
                    r = requests.get(url, stream=True)
                    check = zipfile.is_zipfile(io.BytesIO(r.content))
                attempts += 1
                if attempts == URL_ATTEMPTS_MAX:
                    break
            else:
                try:
                    z = zipfile.ZipFile(io.BytesIO(r.content))
                except Exception as err:
                    print('Could not unzip: ' + err)
                    continue
                z.extractall(dir_name)
    else:
        print(dir_name + ' already exists')


def getDirName(url: str):
    """
    Gets the directory name from the download url
    
    Args:
        url (str): the url where the USC releasepoint zip is stored
    
    Returns:
        str: the directory name corresponding to this releasepoint 
    """
    return url.split('@')[1].split('.')[0]


def getReleaseDate(urlText: str):
    try:
        releaseDate = re.search(r'([0-9]{2}\/[0-9]{2}\/[0-9]{4})', urlText).group(0)
    except:
        releaseDate = None
    return releaseDate


def getTitlesAffected(urlText: str):
    titlesAffected = re.search(
        r'affecting\stitles?(.*)\.?$', urlText).group(1).strip().replace(
            '.', '').replace('and', ',').replace(' ', '').split(',')
    return [item for item in titlesAffected if item]


def getUSCReleasePoints(writeToFile: bool=True):
    # Get current release point, linked from https://uscode.house.gov/download/download.shtml, 
    # e.g. https://uscode.house.gov/download/releasepoints/us/pl/116/65/xml_uscAll@116-65.zip
    current_usc_html_resp = requests.get(USC_HTML_PAGE_BASE + CURRENT_USC_HTML_PAGE)
    if (current_usc_html_resp.status_code == 200):
        current_soup = BeautifulSoup(current_usc_html_resp.content, features="lxml")
    else:
        print('Could not get page from: ' + USC_HTML_PAGE_BASE + USC_HTML_PAGE)
        return

    title_h3 = current_soup.find('h3', attrs={'class': 'releasepointinformation'})
    release_date = getReleaseDate(title_h3.getText())
    current_name_div = current_soup.findAll('div', attrs={'class', 'uscitem'})[1].find('div', attrs={'class': 'itemcurrency'})
    if current_name_div:
        current_name = current_name_div.getText().strip()
    titles_affected_divs = current_soup.findAll('div', attrs={'class': 'usctitlechanged'})
    if titles_affected_divs and len(titles_affected_divs) > 0:
        titlesAffected = [t.attrs.get('id').replace('us/usc/t', '') for t in titles_affected_divs] 
    else:
        titlesAffected = []

    downloadlinks_div = current_soup.find('div', attrs={'class': 'itemdownloadlinks'}).find('a')
    if downloadlinks_div:
        downloadlink = downloadlinks_div.attrs.get('href')

    current_releasepoint = {
            'name': current_name,
            'date': release_date, 
            'titlesAffected': titlesAffected,
            'url': USC_HTML_PAGE_BASE + downloadlink 
        }

    usc_html_resp = requests.get(USC_HTML_PAGE_BASE + USC_HTML_PAGE)
    if (usc_html_resp.status_code == 200):
        soup = BeautifulSoup(usc_html_resp.content, features="lxml")
    else:
        print('Could not get page from: ' + USC_HTML_PAGE_BASE + USC_HTML_PAGE)
        return
    downloadLinks = soup.findAll('a', attrs={'class': 'releasepoint'})
    releasepoints = [
        {
            'name':
            getDirName(link.attrs.get('href')),
            'date':
            getReleaseDate(link.getText()),
            'titlesAffected':
            getTitlesAffected(link.getText()),
            'url':
            USC_HTML_PAGE_BASE + re.sub(r"\.html?$", ".zip",
                                        link.attrs.get('href')).replace(
                                            USC_RP_TEXT, USC_XML_TEXT)
        } for link in downloadLinks
        if re.search(r'([0-9]{2}\/[0-9]{2}\/[0-9]{2})', link.getText())
    ]
    releasepoints.insert(0, current_releasepoint)
    try:
        if writeToFile:
            with open(USC_RELEASEPOINT_JSON_PATH, 'w') as f:
                json.dump(releasepoints, f)
    except Exception as err:
        logger.error(str(err))

    return releasepoints

    #else: print('Could not download releasepoint at: ' + url)
    #           continue


def downloadUSCReleasepointZips(redownload: bool=False):
    releasepoints = getUSCReleasePoints()
    for index, releasepoint in enumerate(releasepoints, start=1):
        url = releasepoint.get('url')
        if url and index!=len(releasepoints):
            dir_name = os.path.join(USC_RELEASEPOINT_DIRPATH,
                                    releasepoint.get('name'))
            getAndUnzipURL(url, dir_name, titlesAffected=releasepoint.get('titlesAffected'), redownload=redownload)
    # Download all titles for the oldest releasepoint
    getAndUnzipURL(url, dir_name, titlesAffected=['All'], redownload=redownload)


def processUSCReleasePoints(download: bool=True, redownload: bool=False, loglevel: str='DEBUG'):
    '''
    Process USC Release Points from uscode.house.gov
    '''

    saved_args = locals()

    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s', args.loglevel)

    if loglevel == 'DEBUG':
        levelvar = logging.DEBUG
    if loglevel == 'INFO':
        levelvar = logging.INFO
    if loglevel == 'WARNING':
        levelvar = logging.WARNING
    if loglevel == 'ERROR':
        levelvar = logging.ERROR

    logging.basicConfig(filename='import.log', filemode='w', level=levelvar)
    logging.getLogger().addHandler(logging.StreamHandler())

    logger.info('Processing USC release points...')
    logger.info(json.dumps(saved_args))
    logger.info('===================')

    if download:
        downloadUSCReleasepointZips(redownload=redownload)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download USC versions.', epilog='')
    parser.add_argument(
        '-d',
        '--debug',
        action='store',
        dest='loglevel',
        default='ERROR',
        help='Set the debug level (default: %(default)s)')

    args = parser.parse_args()

    logger.info(json.dumps(args.__dict__))
    logger.info('===============================')

    processUSCReleasePoints(**args.__dict__)