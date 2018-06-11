import logging, sys, os, requests, json, re
from collections import Counter
from math import exp
import networkx as nx
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from github import Github
logging.basicConfig(format='%(asctime)s | %(levelname)s : %(message)s',
                     level=logging.INFO, stream=sys.stdout)

def enc (word):
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
                print (key)
                
class SetWithFilter(set):
    def lemma(self, value): return set(i for i in self if i.lemma == value)
    def lang(self, value): return set(i for i in self if i.lang == value)

class FilteredList(list):
    def lemma(self, value): return list(i for i in self if i.lemma == value)
    def lang(self, value): return list(i for i in self if i.lang == value)


def l(lang, mode=3):
    mode = mode % 2
    if len(lang)==2:
        if lang in lang_codes[mode]: return lang_codes[mode][lang]
        else: return lang
    else: return lang

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
    if not os.path.exists('./dictionaries/'): os.makedirs('./dictionaries/')
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
    logging.info('finished')
                    
def check (word1, word2, lang1, lang2):
    word1 = lang1[word1]
    word2 = lang2[word2]
    return word1, word2

def one_word2(word, lang):
    s = word.findall('.//s')
    s = [i.attrib['n'] for i in s]
    if word.text: st = str(word.text)
    else: st = ''
    s = Tags(s)
    if '_' in st: st = st.replace('_',' ')
    return Word(st, lang, s)

def parse_bidix (tree, l1, l2):
    tree = tree.find('section')
    if not tree: pass
    else:
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
    if pair[0] in nodes and pair[1] in nodes: return True
    else: return False

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
def import_mono(lang):
    dictionary = DiGetItem()
    with open ('./monodix/{}.dix'.format(lang), 'r', encoding='utf-16') as f:
        for line in f:
            string = line.strip('\n').split('\t')
            s = [Tags([j for j in i.split('-') if j !='']) for i in string[1].strip().split('$')]
            dictionary.add(Word(string[0], lang, s))
    return dictionary
	
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
    #print (d)
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

