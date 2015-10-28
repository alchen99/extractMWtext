#!/usr/bin/python

# Tested with MediaWiki 1.22.7

import requests
import xml.etree.ElementTree as ET

NS      = {'mw': 'http://www.mediawiki.org/xml/export-0.8/'}
user    = 'WIKI_USER_WITH_API_PRIV'
passw   = 'WIKI_USER_PASSWORD'
baseurl = 'WIKI_BASE_URL'
params  = '?action=login&lgname=%s&lgpassword=%s&format=json'% (user,passw)

UNICODE_REPLACEMENTS = {
    u"\u2010": u"-",    # Hyphen
    u"\u2011": u"-",    # Non-breaking hyphen
    u"\u2013": u"-",    # Figure dash
    u"\u2013": u"-",    # En-dash
    u"\u2014": u"-",    # Em-dash
    u"\u2015": u"-",    # Horizontal bar
    u"\u2212": u"-",    # Minus sign

    u"\u00b4": u"'",    # Acute accent
    u"\u2018": u"'",    # Left single quote
    u"\u2019": u"'",    # Right single quote
    u"\u201c": u'"',    # Left double quote
    u"\u201d": u'"',    # Right double quote

    u"\u00b7": u"*",    # Middle dot
    u"\u2022": u"*",    # Bullet
    u"\u2023": u">",    # Triangular bullet
    u"\u2024": u"*",    # One dot leader
    u"\u2026": '...',   # Triple elipses
    u"\u2043": u"-",    # Hyphen bullet
    u"\u25b8": u">",    # Black right-pointing small triangle
    u"\u25e6": u"o",    # White bullet
    u"\xa0": u" ",      # space 
}

#---------------------------------------------------------
# Login to Mediawiki
#---------------------------------------------------------

# Login request
r1 = requests.post(baseurl+'api.php'+params)
token = r1.json()['login']['token']
params2 = params+'&lgtoken=%s'% token

# Confirm token; should give "Success"
r2 = requests.post(baseurl+'api.php'+params2,cookies=r1.cookies)


#----------------------------------------------------------
# Look at Special:AllPages to see what wiki pages we have
#----------------------------------------------------------
ra = requests.get(baseurl + 'index.php/Special:AllPages')
wikiAll = ET.fromstring(ra.text)
#ET.dump(wikiAll)
for td in wikiAll.findall('.//*[@id="mw-content-text"]/table[2]/tr/td'):
    atag = td.find('a')
    #ET.dump(atag)
    wikiFoundPage = atag.attrib['href'][16:]
    # ignore translated pages for now
    if not wikiFoundPage.endswith(('/en', '/zh-hans', '/zh-hant', 'Translations_Practice_Page')):
        #-------------------------------------------------------
        # Fetch each MW page in wiki format
        #-------------------------------------------------------
        print "Extracting wikitext from page " + wikiFoundPage
        r3 = requests.get(baseurl + 'index.php/Special:Export/' + wikiFoundPage)
        pXML = r3.text

        #------------------------------------------------------------------------------
        # our wiki contains some unicode characters that need to be converted
        # to their ascii equivalent. Otherwise these unicode characters will cause
        # fromstring to fail
        #------------------------------------------------------------------------------

        for src, dst in UNICODE_REPLACEMENTS.iteritems():
            pXML = pXML.replace(src, dst)
            
        # double and single quotes
        #pXML = r3.text.replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\u201c",'"').replace(u"\u201d",'"')
        # triple elipses and dash
        #pXML = pXML.replace(u"\u2026","...").replace(u"\u2013","-").replace(u"\xa0",u" ")
        root = ET.fromstring(pXML)

        # long (dynamic) way to find an element
        #page = root.find('mw:page', NS)
        #revision = page.find('mw:revision', NS)
        #wikitxt = revision.find('mw:text', NS)

        # short way to find an element if we know XML tree structure
        wikiTxt = root.find('mw:page/mw:revision/mw:text', NS)

        # write out wikiTxt to file
        with open (wikiFoundPage + '.wiki', 'w+') as wikiFile:
            wikiFile.write(wikiTxt.text)
