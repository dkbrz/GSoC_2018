import logging
import sys
import os
import requests

logging.basicConfig(format='%(asctime)s | %(levelname)s : %(message)s',
                     level=logging.INFO, stream=sys.stdout)
import json
import re
#from collections import Counter
#from math import exp


#import networkx as nx
import xml.etree.ElementTree as ET

#from collections import Counter, defaultdict
from github import Github

def l(lang, mode=3):
    mode = mode % 2
    if len(lang)==2:
        if lang in lang_codes[mode]:
            return lang_codes[mode][lang]
        else:
            return lang
    else:
        return lang

def repo_names(user):
    for repo in user.get_repos():
        if re.match('apertium-[a-z]{2,3}(_[a-zA-Z]{2,3})?-[a-z]{2,3}(_[a-zA-Z]{2,3})?', repo.name):
            yield repo.name    

def bidix_url(repo):
    for i in sorted(repo.get_dir_contents('/'), key = lambda x: (len(x.path), 1000-ord(('   '+x.path)[-3])), reverse=True):
        if re.match('apertium-.*?\.[a-z]{2,3}(_[a-zA-Z]{2,3})?-[a-z]{2,3}(_[a-zA-Z]{2,3})?.dix$', i.path): return i.download_url
        elif len(i.path) < 23: return None

def download_all_bidixes():
    global lang_codes
    with open ('./files/lang_codes.json', 'r') as f:
        lang_codes = json.load(f)
    
    with open ('secure.json') as f:
        SECRET = json.loads(f.read())
    github = Github(SECRET['USER'], SECRET['PASSWORD'])
    user = github.get_user('apertium')
    logging.info('Start')
    if not os.path.exists('./dictionaries/'):
        os.makedirs('./dictionaries/')
    for repo_name in repo_names(user):
        bidix = bidix_url(github.get_repo(user.name+'/'+repo_name))
        langs = [l(i) for i in repo_name.split('-')[1:]]
        filename = './dictionaries/'+'-'.join(langs)+'.dix'
        if bidix:
            response = requests.get(bidix)
            response.encoding = 'UTF-8'
            with open(filename, 'w', encoding='UTF-8') as f:
                f.write(response.text)
    logging.info('Finish')        
