import logging, sys, os, requests, json, re
from collections import Counter
from math import exp, log10
from itertools import islice
import networkx as nx
import xml.etree.ElementTree as ET
from github import Github
logging.basicConfig(format='%(asctime)s | %(levelname)s : %(message)s',
                     level=logging.INFO, stream=sys.stdout)
from itertools import islice
import matplotlib.pyplot as plt
from heapdict import heapdict
from tqdm import tqdm_notebook as tqdm
import random
import numpy as np, scipy.stats as st


# CLASSES

# delete?
def enc (word):
    "Check encoding"
    s = word.encode('utf-8')
    s = s.decode('utf-8')
    return s

class Word:
    def __init__(self, lemma, lang, s=[]):
        if lemma == None: self.lemma = ''
        else: self.lemma = enc(lemma)
        self.lang = lang
        self.s = s
        
    def __str__(self):
        if self.s:
            if isinstance(self.s[0],list): w = '['+'_'.join(['-'.join(i) for i in self.s])+']'
            else: w = '['+'-'.join(self.s)+']'
        else: w = '-'
        return str(self.lang)+'$'+str(self.lemma)+'$'+str(w)
    
    __repr__ = __str__
    
    def __eq__(self, other):
        return self.lemma == other.lemma and self.lang == other.lang and (self.s == other.s or other.s in self.s or self.s in other.s)
    
    def __lt__(self, other):
        if self.lang == other.lang:
            if self.lemma == other.lemma:
                s1 = set(self.s)
                s2 = set(other.s)
                if (not s1 - s2) and (s1&s2==s1) and (s2 - s1): return True
                else: return False
        else: return False
    
    def __hash__(self): return hash(str(self))
    
    def write(self, mode='mono'):
        "Mono: format to write in monodix, bi: format to write in bidix"
        if mode == 'mono': return self.lemma + '\t' + '$'.join([str(i) for i in self.s])
        elif mode == 'bi': return self.lang + '\t' +  self.lemma + '\t' + '$'.join([str(i) for i in self.s])
              
class Tags(list):
    def __le__(self, other):
        s1 = set(self)
        s2 = set(other)
        if not s1 - s2 and s1&s2==s1: return True
        else: return False
    
    def __lt__(self, other):
        s1 = set(self)
        s2 = set(other)
        if (not s1 - s2) and (s1&s2==s1) and (s2 - s1): return True
        else: return False
    
    def __eq__(self, other):
        if set(self) == set(other): return True
        else: return False
        
    def __str__(self): return '-'.join(self)
    
    __repr__ = __str__
    
    def __hash__(self): return hash(str(self))
    
class WordDict(dict):
    def lemma(self, lemma): self.lemma = lemma
        
class FilteredDict(dict):
    def set_lang(self, lang): self.lang = lang
    
    def lemma(self, lemma): return self[self.lang+'_'+lemma]
        
    def add(self, word):
        lemma = word.lang+'_'+word.lemma
        tags = Tags(word.s)
        if lemma in self:
            if tags in self[lemma]: self[lemma][tags] += 1
            else: self[lemma][tags] = 1
        else:
            self[lemma] = WordDict()
            self[lemma].lemma(lemma)
            self[lemma][tags] = 1
            
class DiGetItem:
    def __init__(self):
        self.list = []
        self.dict = {}
    
    def add(self, word):
        if len (word.s) > 1: self.list.append(word)
        else: self.dict[word] = word
    
    def __getitem__(self, key):
        key2 = Word(key.lemma, key.lang, [''])
        if key in self.dict: return self.dict[key]
        else:
            if key2 in self.dict: return self.dict[key2]
            try:
                key = self.list[self.list.index(key)]
                return key
            except:
                pass
    def __len__(self):
        return len(self.list)+len(self.dict)
                
class SetWithFilter(set):
    def lemma(self, value): return set(i for i in self if i.lemma == value)
    def lang(self, value): return set(i for i in self if i.lang == value)

class FilteredList(list):
    def lemma(self, value): return list(i for i in self if i.lemma == value)
    def lang(self, value): return list(i for i in self if i.lang == value)

class DictionaryStats:
    def __init__(self, file):
        self.file = file
        self.name1 = file.replace('.dix','').split('-')[0]
        self.name2 = file.replace('.dix','').split('-')[1]
        self.mono1 = import_mono(self.name1)
        self.mono2 = import_mono(self.name2)
        self.count = [0,0,0] #both, LR, RL
        #self.set1 = set()
        #self.set2 = set()
        self.get_data()
    
    def get_data(self):
        with open ('./dictionaries/'+self.file, 'r', encoding='utf-8') as d:
            with open ('./parsed/'+self.file, 'w', encoding='utf-8') as copy:
                try:
                    tree = ET.fromstring(re.sub('\s{3,}','\t', d.read().replace('<b/>',' ').replace('<.?g>','')))
                    for word1, word2, side in parse_bidix (tree, self.name1, self.name2):
                        try:
                            word1, word2 = check (word1, word2, self.mono1, self.mono2)
                            
                            #if word1 not in self.set1: 
                            #    self.count1 += 1
                            #    self.set1.add(word1)
                            #if word2 not in self.set2:
                            #    self.count2 += 1
                            #    self.set2.add(word2)   
                            #self.count += 1
                            if not side:
                                self.count[0]+=1
                            elif side == 'LR':
                                self.count[1] += 1
                            elif side == 'RL':
                                self.count[2] += 1
                            string = str(side) + '\t' + word1.write(mode='bi') + '\t' + word2.write(mode='bi') + '\n'
                            copy.write(string)
                        except: pass
                except: pass
            
    def get_stats(self):
        return self.count

# LOADING

def l(lang, mode=3):
    "Language code converter"
    if lang in lang_codes: return lang_codes[lang]
    else: return lang
    #mode = mode % 2
    #if len(lang)==2:
    #    if lang in lang_codes[mode]: return lang_codes[mode][lang]
    #    else: return lang
    #else: return lang

def repo_names(user):
    "List of language pair repos in Apertium"
    for repo in user.get_repos():
        if re.match('apertium-[a-z]{2,3}(_[a-zA-Z]{2,3})?-[a-z]{2,3}(_[a-zA-Z]{2,3})?', repo.name):
            yield repo.name

def bidix_url(repo):
    "Find raw url for bidix. Sorting in order to find bidix faster as it is one of the longest filename in repo"
    for i in sorted(repo.get_dir_contents('/'), key = lambda x: (len(x.path), 1000-ord(('   '+x.path)[-3])), reverse=True):
        if re.match('apertium-.*?\.[a-z]{2,3}(_[a-zA-Z]{2,3})?-[a-z]{2,3}(_[a-zA-Z]{2,3})?.dix$', i.path): return i.download_url
        elif len(i.path) < 23: return None

def download_all_bidixes():
    "Copy all bidixes from Apertium Github and save in dictionary folder"
    global lang_codes
    with open ('./files/lang_codes.json', 'r') as f: lang_codes = json.load(f)
    
    with open ('secure.json') as f: SECRET = json.loads(f.read())
    github = Github(SECRET['USER'], SECRET['PASSWORD'])  #import username and password
    user = github.get_user('apertium')
    
    logging.info('Start')
    if not os.path.exists('./dictionaries/'): os.makedirs('./dictionaries/')
    for repo_name in repo_names(user):
        bidix = bidix_url(github.get_repo(user.name+'/'+repo_name))
        langs = [l(i) for i in repo_name.split('-')[1:]]
        filename = './dictionaries/'+'-'.join(langs)+'.dix'
        if bidix:
            response = requests.get(bidix)
            response.encoding = 'UTF-8'
            with open(filename, 'w', encoding='UTF-8') as f: f.write(response.text)
    logging.info('Finish')        

# PREPROCESSING AND BUILDING

def one_language_dict(lang):
    "Gather dictionary of one language from bidixes"
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
                    for word in parse_one(t, side, lang): dictionary.add(word)
                except: pass
    return dictionary

def shorten(word_dict):
    "Categorize tags into groups that do not show conflicts like n|n-m|n-m-sg. Priority to most frequent."
    short = []
    for i in sorted(word_dict, key=lambda x: (word_dict[x], -len(x)), reverse=True):
        new, add = True, True
        for key, j in enumerate(short):
            if not add: break
            inner = True
            for key2, k in enumerate(j):
                if (k < i) or (i < k): pass
                else: inner = False
            if inner: 
                short[key].append(i)
                new = False
                add = False
        if new: short.append([i])
    word = word_dict.lemma[4:]
    return word, short

def one_word(word, lang):
    "One word parsing: lemma, tags, wrap in Word class"
    if word.text: st = str(word.text)
    else: st = ''
    s = [i.attrib['n'] for i in word.findall('.//s')]
    s = [i for i in s if i != '']
    return Word(st, lang, s)

def parse_one (tree, side, lang):
    "One dictionary parsing: yield all words"
    all = tree.findall('section')
    for tree in all:
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
    "In one language dict yield all words so to write them later"
    for i in dictionary.keys():
        word, tags = shorten(dictionary[i])
        if '_' in word:
            word = word.replace('_', ' ')
        for tag in tags:
            yield Word(word, dictionary.lang, Tags([i for i in tag if i != '']))
                      
def monodix():
    "Create all monodixes and add them to monodix folder"
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
    logging.info('finished')
                    
def check (word1, word2, lang1, lang2):
    "Check full words. Input: word with one tag variant (n-m). Output: full tags (n|n-m|n-m-sg)"
    word1 = lang1[word1]
    word2 = lang2[word2]
    return word1, word2

def one_word2(word, lang):
    "One word parsing in bidix"
    s = word.findall('.//s')
    s = [i.attrib['n'] for i in s]
    if word.text: st = str(word.text)
    else: st = ''
    s = Tags(s)
    if '_' in st: st = st.replace('_',' ')
    return Word(st, lang, s)

def parse_bidix (tree, l1, l2):
    "Parse bidix: lines into two words."
    all = tree.findall('section')
    if not all: pass
    else:
        for tree in all:
            for e in tree:
                if 'r' in e.attrib: side = e.attrib['r']
                else: side = ''
                p = e.find('p')
                if p:
                    yield one_word2(p.find('l'), l1), one_word2(p.find('r'), l2), side
                else:
                    i = e.find('i')
                    if i:
                        yield one_word2(i, l1), one_word2(i, l2), side

def existance(pair, nodes):
    "Check if language pair links two languages from our list"
    if pair[0] in nodes and pair[1] in nodes: return True
    else: return False

def preprocessing():
    if not os.path.exists('./parsed/'):
        os.makedirs('./parsed/')
    with open ('./files/stats.csv','w', encoding='utf-8') as outp:
        #outp.write('{}\t{}\t{}\t{}\t{}\n'.format('lang1','lang2','total','1','2'))
        for root, dirs, files in os.walk('./dictionaries/'):
            for fl in tqdm(files):
                try:
                    pair = fl.replace('.dix','').split('-')
                    outp.write ('\t'.join(pair) + '\t'+ '\t'.join([str(i) for i in DictionaryStats(fl).get_stats()])+'\n')
                except:
                    pass

def import_mono(lang):
    "Import monodix. Parse all lines, split them and get a dictionary of them to have all nodes in one place."
    dictionary = DiGetItem()
    with open ('./monodix/{}.dix'.format(lang), 'r', encoding='utf-16') as f:
        for line in f:
            string = line.strip('\n').split('\t')
            s = [Tags([j for j in i.split('-') if j !='']) for i in string[1].strip().split('$')]
            dictionary.add(Word(string[0], lang, s))
    return dictionary
	
def change_encoding(file):
    "Change utf-16 that works with accents inside program to utf-8 to reduce file size (doesn't cause problems in this case)"
    with open(file, 'r', encoding='utf-16') as f:
        text = f.read()
    text = text.encode('utf-8')
    text = text.decode('utf-8')
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)

def get_relevant_languages(l1, l2):
    "Get relevant languages to choose from when creating a graph (configuration file). Firstly, there go closer languages in graph of existing bidixes (from most connected in general) then more distant."
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
            if pair[1] in H.nodes(): v = nx.node_connected_component(H, pair[1])
            else: v = set()
            if pair[0] in H2.nodes(): w = nx.node_connected_component(H, pair[1])
            else: w = set() 
            nodes2 = v & w | set([pair[0], pair[1]])
            nodes2 = nodes2 - nodes
            for lang in languages:
                if lang in nodes2: f.write('{}\t{}\n'.format(i*2, lang))
            nodes = nodes | nodes2

def all_languages():
    G = nx.Graph()
    for root, dirs, files in os.walk ('./dictionaries/'):
        for fl in files :
            pair = fl.replace('.dix', '').split('-')
            G.add_edge(pair[0], pair[1])
    d = dict(G.degree())
    d = sorted(d, key=d.get, reverse=True)
    with open('languages','w',encoding='utf-8') as f:
        f.write('\t'.join(d))

def parse_line(line):
    side, lang1, lemma1, tags1, lang2, lemma2, tags2 = line.strip('\n').split('\t')
    tags1 = [Tags(i.split('-')) for i in tags1.split('$')]
    tags2 = [Tags(i.split('-')) for i in tags2.split('$')]
    return side, Word(lemma1, lang1, tags1), Word(lemma2, lang2, tags2)

def nodes_from_file(file):
    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            yield parse_line(line)
            
def built_from_file(file):
    G = nx.DiGraph()
    for side, word1, word2 in nodes_from_file(file):
        if not side:
            G.add_edge(word1, word2)
            G.add_edge(word2, word1)
        elif side == 'LR': G.add_edge(word1, word2)
        elif side == 'RL': G.add_edge(word2, word1)
        else: pass #print (side)
    return G

def dictionaries(lang1,lang2):
    l1 = import_mono(lang1)
    l2 = import_mono(lang2)
    l1 = SetWithFilter(l1.list+list(l1.dict.keys()))
    l2 = SetWithFilter(l2.list+list(l2.dict.keys()))
    return l1, l2

# SEARCH

def _single_shortest_path_length(adj, firstlevel, cutoff, lang, n):
    """ Variant of NetworkX function _single_shortest_path_length"""
    seen = {}                  # level (number of hops) when seen in BFS
    level = 0                  # the current level
    nextlevel = firstlevel     # dict of nodes to check at next level
    k = 0
    while nextlevel and cutoff >= level and k < n:
        thislevel = nextlevel  # advance to next level
        nextlevel = {}         # and start a new list (fringe)
        for v in thislevel:
            if v not in seen:
                seen[v] = level  # set the level of vertex v
                if v.lang == lang: 
                    k += 1
                    yield v
                else: nextlevel.update(adj[v])
        level += 1
    del seen

def possible_translations(G, source, lang, cutoff=4, n = 20):
    """ Variant of NetworkX function single_source_shortest_path_length"""
    if source not in G: raise nx.NodeNotFound('Source {} is not in G'.format(source))
    if cutoff is None: cutoff = float('inf')
    nextlevel = {source: 1}
    return list(_single_shortest_path_length(G.adj, nextlevel, cutoff, lang, n))

def sorting(result, n):
    result = [(x, result[x]) for x in sorted(result, key=result.get, reverse=True)[:n]]
    return result

def print_results(results, n=7):
    for i in results:
        print ('\n\t\t', i)
        for j in sorted(results[i], key=results[i].get, reverse=True)[:n]:
            print (j, results[i][j])

def print_lemma_results(results, n=10):
    for i in results:
        print ('\t\t', i)
        words = sorting(results[i], n)
        for j in words:
            print ('{}\t{}'.format(j[0], j[1]))
        print()

def get_relevant_languages(source, target):
    G = nx.Graph()
    with open ('./files/stats.csv', 'r', encoding='utf-8') as f:
        for line in f:
            data = line.split('\t')
            coef = 1/log10(10+float(data[2])+0.5*float(data[3])+0.5*float(data[4]))
            if coef < 1:
                G.add_edge(data[0], data[1], weight=coef)
    result = {}
    for path in islice(nx.shortest_simple_paths(G, source=source, target=target, weight='weight'), 0, 300):
        length = sum([G[path[i]][path[i-1]]['weight'] for i in range(1, len(path))])
        for node in path:
            if node not in result:
                result[node]  = (length, path)
    with open ('language_list.csv','w', encoding='utf-8') as f:
        for i in sorted(result, key=result.get):
            f.write(str(result[i][0])+'\t'+str(i)+'\t:\t'+' '.join(result[i][1])+'\n')

def load_file(l1,l2, n=10000):
    with open ('language_list.csv','r',encoding='utf-8') as f:
        languages = set([i.split('\t')[1].strip() for i in islice(f.readlines(), 0, n)])
    languages = languages | set([l1,l2])
    with open ('{}-{}'.format(l1, l2), 'w', encoding='utf-16') as f:
        for root, dirs, files in os.walk ('./parsed/'):
            for fl in files:
                pair = fl.replace('.dix','').split('-')
                if existance(pair, languages):
                    #print (pair)
                    with open (root+fl, 'r', encoding='utf-8') as d:
                        f.write(d.read())

def check_graph(l1, l2, n=10):
    G = nx.Graph()
    with open ('./files/stats.csv', 'r', encoding='utf-8') as f:
        for line in f:
            data = line.split('\t')
            coef = 1/log10(10+float(data[2])+0.5*float(data[3])+0.5*float(data[4]))
            if coef < 1:
                G.add_edge(data[0], data[1], weight=coef)
    with open ('language_list.csv','r',encoding='utf-8') as f:
        languages = set([i.split('\t')[1].strip() for i in islice(f.readlines(), 0, n)])
    languages = languages | set([l1,l2])
    nx.draw_shell(G.subgraph(languages), with_labels = True, font_size = 20, node_color = 'white')

