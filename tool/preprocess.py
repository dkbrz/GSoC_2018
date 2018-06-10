import logging
import sys
import os
import requests

logging.basicConfig(format='%(asctime)s | %(levelname)s : %(message)s',
                     level=logging.INFO, stream=sys.stdout)
import json
import re
import networkx as nx 
from tool.classes import *
import xml.etree.ElementTree as ET
from tool.classes import *
from tool.general import *

def one_language_dict(lang):
    dictionary = FilteredDict()
    dictionary.set_lang(lang)
    for root, dirs, files in os.walk ('./dictionaries/'):
        for fl in files :
            pair = fl.replace('.dix','').split('-')
            if lang in pair:
                if lang == pair[0]: side = 'l'
                else: side = 'r'
                try:
                    with open (root+fl, 'r', encoding='utf-8') as d:
                        t = ET.fromstring(d.read().replace('<b/>',' ').replace('<.?g>',''))     
                    for word in parse_one(t, side, lang):
                        dictionary.add(word)
                except:
                    pass
                #with open (root+fl, 'r', encoding='utf-8') as d:
                #    t = ET.fromstring(d.read().replace('<b/>',' ').replace('<.?g>',''))     
                #for word in parse_one(t, side, lang):
                #    dictionary.add(word)
    return dictionary

def shorten(word_dict):
    short = []
    for i in sorted(word_dict, key=lambda x: (word_dict[x], -len(x)), reverse=True):
        new = True
        for key, j in enumerate(short):
            inner = True
            for key2, k in enumerate(j):
                if (k < i) or (i < k): pass
                else: inner = False
            if inner: 
                short[key].append(i)
                new = False
        if new: short.append([i])
    word = word_dict.lemma[4:]
    return word, short


def one_word(word, lang):
    if word.text: st = str(word.text)
    else: st = ''
    s = [i.attrib['n'] for i in word.findall('.//s')]
    s = [i for i in s if i != '']
    return Word(st, lang, s)

def parse_one (tree, side, lang):
    tree = tree.find('section')
    for e in tree:
        p = e.find('p')
        if p:
            word = one_word(p.find(side), lang)
            yield word
        else:
            i = e.find('i')
            if i:
                word = one_word(i, lang)
                yield word
            else:
                pass
            
def dictionary_to_nodes(dictionary):
    for i in dictionary.keys():
        word, tags = shorten(dictionary[i])
        if '_' in word:
            word = word.replace('_', ' ')
        for tag in tags:
            yield Word(word, dictionary.lang, Tags([i for i in tag if i != '']))
            
            
def monodix():
    all_languages()
    logging.info('started')
    if not os.path.exists('./monodix/'):
        os.makedirs('./monodix/')
    with open('languages','r', encoding='utf-8') as f:
        langs = f.read().split('\t')
    for lang in langs:
        dictionary = one_language_dict(lang)
        with open ('./monodix/'+lang+'.dix', 'w', encoding = 'utf-16') as f:
            for i in dictionary_to_nodes(dictionary):
                f.write (i.write(mode='mono')+'\n')
        #logging.info(lang)
    logging.info('finished')
                    
def check (word1, word2, lang1, lang2):
    #word1 = lang1[lang1.index(word1)]
    #word2 = lang2[lang2.index(word2)]
    word1 = lang1[word1]
    word2 = lang2[word2]
    return word1, word2

def one_word2(word, lang):
    s = word.findall('.//s')
    s = [i.attrib['n'] for i in s]
    if word.text: st = str(word.text)
    else: st = ''
    s = Tags(s)
    if '_' in st:
        st = st.replace('_',' ')
    return Word(st, lang, s)

def parse_bidix (tree, l1, l2):
    tree = tree.find('section')
    if not tree:
        pass
        #print (l1, l2)
    else:
        for e in tree:
            if 'r' in e.attrib:
                side = e.attrib['r']
                #print (side)
            else:
                side = ''
            p = e.find('p')
            if p:
                yield one_word2(p.find('l'), l1), one_word2(p.find('r'), l2), side
            else:
                i = e.find('i')
                if i:
                    yield one_word2(i, l1), one_word2(i, l2), side

def existance(pair, nodes):
    if pair[0] in nodes and pair[1] in nodes:
        return True
    else:
        return False

def load_file(l1, l2):
    with open ('language_list.csv','r',encoding='utf-8') as f:
        languages = set([i.split('\t')[1].strip() for i in f.readlines()])
    with open ('{}-{}'.format(l1, l2), 'w', encoding='utf-16') as f:
        for root, dirs, files in os.walk ('./dictionaries/'):
            for fl in files:
                pair = fl.replace('.dix','').split('-')
                if existance(pair, languages):
                    logging.info('{}-{} started'.format(pair[0], pair[1]))
                    lang1 = import_mono(pair[0])
                    lang2 = import_mono(pair[1])
                    with open (root+fl, 'r', encoding='utf-8') as d:
                        try:
                            tree = ET.fromstring(d.read().replace('<b/>',' ').replace('<.?g>',''))
                            for word1, word2, side in parse_bidix (tree, pair[0], pair[1]):
                                try:
                                    word1, word2 = check (word1, word2, lang1, lang2)
                                    string = str(side) + '\t' + word1.write(mode='bi') + '\t' + word2.write(mode='bi') + '\n'
                                    f.write(string)
                                    #if side:
                                    #    print (string)
                                except:
                                    pass
                        except:
                            print ('ERROR: {}-{}'.format(pair[0], pair[1]))
                            
def change_encoding(file):
    with open(file, 'r', encoding='utf-16') as f:
        text = f.read()
    text = text.encode('utf-8')
    text = text.decode('utf-8')
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)

def get_relevant_languages(l1, l2):
    G = nx.Graph()
    for root, dirs, files in os.walk ('./dictionaries/'):
        for fl in files :
            pair = fl.replace('.dix', '').split('-')
            G.add_edge(pair[0], pair[1])
    pair = [l1, l2]
    
    with open('languages','r', encoding='utf-8') as f:
        languages = f.read().split('\t')
        
    with open('language_list.csv','w', encoding='utf-8') as f:
        nodes = set()
        for i in range(1,5):
            w = nx.single_source_shortest_path_length(G, pair[0], cutoff=i)
            v = nx.single_source_shortest_path_length(G, pair[1], cutoff=i)
            H = G.subgraph(w.keys()).copy()
            H.remove_node(pair[0])
            H2 = G.subgraph(v.keys()).copy()
            H2.remove_node(pair[1])
            if pair[1] in H.nodes():
                v = nx.node_connected_component(H, pair[1])
            else:
                v = set()
            if pair[0] in H2.nodes():
                w = nx.node_connected_component(H, pair[1])
            else:
                w = set() 
            nodes2 = v & w | set([pair[0], pair[1]])
            nodes2 = nodes2 - nodes
            for lang in languages:
                if lang in nodes2:
                    f.write('{}\t{}\n'.format(i*2, lang))
            nodes = nodes | nodes2

def all_languages():
    G = nx.Graph()
    for root, dirs, files in os.walk ('./dictionaries/'):
        for fl in files :
            pair = fl.replace('.dix', '').split('-')
            G.add_edge(pair[0], pair[1])
    d = dict(G.degree())
    d = sorted(d, key=d.get, reverse=True)
    #print (d)
    with open('languages','w',encoding='utf-8') as f:
        f.write('\t'.join(d))