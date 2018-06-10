import logging
import sys
import os
import requests

logging.basicConfig(format='%(asctime)s | %(levelname)s : %(message)s',
                     level=logging.INFO, stream=sys.stdout)
import json
import re


def import_mono(lang):
    dictionary = DiGetItem()
    with open ('./monodix/{}.dix'.format(lang), 'r', encoding='utf-16') as f:
        for line in f:
            string = line.strip('\n').split('\t')
            s = [Tags([j for j in i.split('-') if j !='']) for i in string[1].strip().split('$')]
            dictionary.add(Word(string[0], lang, s))
    return dictionary

