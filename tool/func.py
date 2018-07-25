import logging, sys, os, requests, re
from collections import Counter
from math import exp, log10
from itertools import islice
import networkx as nx
import xml.etree.ElementTree as ET
from github import Github
logging.basicConfig(format='%(asctime)s | %(levelname)s : %(message)s', level=logging.INFO, stream=sys.stdout)
from itertools import islice
import matplotlib.pyplot as plt
from heapdict import heapdict
import random
import numpy as np, scipy.stats as st
from .data import lang_codes, rename, remove
from tqdm import tqdm

# CLASSES

class Word:
    def __init__(self, lemma, lang, s=[]):
        if lemma == None: self.lemma = ''
        else: self.lemma = lemma
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
        if self.lang == other.lang and self.lemma == other.lemma:
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
        elif mode == 'out' and len(self.s)<1: return self.lemma + '\t'+''
        elif mode == 'out'and len(self.s)>=1: return self.lemma + '\t' + str(self.s[0])

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

# LOADING

def l(lang, mode=3):
    "Language code converter"
    if lang in lang_codes: return lang_codes[lang]
    else: return lang

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

def download():
    from tool.secure import SECRET
    github = Github(SECRET['USER'], SECRET['PASSWORD'])  #import username and password
    user = github.get_user('apertium')
    
    logging.info('Started downloading')
    if not os.path.exists('./dictionaries/'): os.makedirs('./dictionaries/')
    for repo_name in repo_names(user):
        bidix = bidix_url(github.get_repo(user.name+'/'+repo_name))
        if bidix:
            try:
                filename = './dictionaries/'+bidix.split('/')[-1]
                response = requests.get(bidix)
                response.encoding = 'UTF-8'
                with open(filename, 'w', encoding='UTF-8') as f: f.write(response.text)
            except:
                pass
    logging.info('Finished downloading')  

def set_github_user(user, password):
    with open ('./tool/secure.py', 'w', encoding='utf-8') as f:
        f.write('SECRET = {"USER": "'+user+'", "PASSWORD": "'+password+'"}')

def list_files(path='./dictionaries/', dialects = False):
    #print (path, dialects)
    from tool.data import remove
    with open ('filelist.txt','w', encoding='utf-8') as f:
        for root, dirs, files in os.walk (path):
            for file in files:
                if re.match('apertium-.*?\.[a-z]{2,3}(_[a-zA-Z]{2,3})?-[a-z]{2,3}(_[a-zA-Z]{2,3})?.dix$', file):
                    name = '-'.join(l(i) for i in file.split('.')[-2].split('-'))
                    if name not in remove:
                        f.write(os.path.abspath(os.path.join(root, file)).replace("\\","/")+'\n')
    if dialects:
        split_dialects()

def split_dialects():
    with open('filelist.txt','r') as f:
        file_list = f.readlines()
    file_list = [i.strip() for i in file_list]
    #print (len(file_list))
    file_list2 = []
    for file in file_list:
        if not os.path.exists('./dictionaries/'): os.makedirs('./dictionaries/')
        filename = file.split('.')[-2].split('-')
        try:
        #if True:
            tree = ET.parse(file)
            result = {}
            for section in tree.findall('section'):
                for i in section:
                    name = []
                    if not 'vl' in i.attrib and not 'vr' in i.attrib:
                        name = [filename[0]+'-'+filename[1]]
                    elif 'vr' in i.attrib and not 'vl' in i.attrib:
                        name = [filename[0]+'-' + l(filename[1]+'_'+j) for j in i.attrib['vr'].split(' ')]
                    elif 'vl' in i.attrib and not 'vr' in i.attrib:
                        name = [l(filename[0]+'_'+j) +'-'+filename[1] for j in i.attrib['vl'].split(' ')]
                    else:
                        for j in i.attrib['vl'].split(' '):
                            for k in i.attrib['vr'].split(' '):
                                name.append(l(filename[0]+'_'+j)+'-'+l(filename[1]+'_'+k))
                    for j in name:
                        if j not in result: result[j] = ET.Element('section')
                        result[j].append(i)

            if len (result) > 1:
                for i in result:
                    nm = i.split('-')
                    nm = './dictionaries/apertium-{}-{}.{}-{}.dix'.format(filename[0], filename[1], nm[0], nm[1])
                    tree = ET.Element('dictionary')
                    tree.append(result[i])
                    ET.ElementTree(tree).write(nm, encoding='utf-8')
                    with open(nm, 'r', encoding='utf-8') as f:
                        xml = f.read()
                    with open(nm, 'w', encoding='utf-8') as f:
                        f.write(xml.replace('<e','\n    <e').replace('</section>','\n</section>'))    
                    file_list2.append(os.path.abspath(nm).replace("\\","/"))
                print ('-'.join(filename))
            else:
                file_list2.append(file)
        except: pass #print ('Error:\t', file.split('.')[-2])
        with open('filelist.txt','w', encoding='utf-8') as f:
            f.write('\n'.join(file_list2))

# PREPROCESSING AND BUILDING

def all_languages():
    s = set()
    with open ('./tool/langs.py','w',encoding='utf-8') as outp:
        with open ('filelist.txt','r',encoding='utf-8') as inp:
            for line in inp:
                name = [l(i) for i in line.split('.')[-2].split('-')]
                s.update(name)
        outp.write('langs='+str(s))

def one_language_dict(lang):
    "Gather dictionary of one language from bidixes"
    dictionary = FilteredDict()
    dictionary.set_lang(lang)
    with open ('./filelist.txt','r', encoding='utf-8') as f:
        for line in f:
            line = line.strip('\n')
            pair = [l(i) for i in line.split('.')[-2].split('-')]
            if '-'.join(pair) in rename: pair = rename['-'.join(pair)].split('-')
            if lang in pair:
                if lang == pair[0]: side = 'l'
                else: side = 'r'
                try:
                    with open (line, 'r', encoding='utf-8') as d:
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
    logging.info('Started monolingual dictionaries')
    if not os.path.exists('./monodix/'):
        os.makedirs('./monodix/')
    #for lang in tqdm(langs):
    for lang in langs:
        dictionary = one_language_dict(lang)
        with open ('./monodix/'+lang+'.dix', 'w', encoding = 'utf-16') as f:
            for i in dictionary_to_nodes(dictionary):
                f.write (i.write(mode='mono')+'\n')
    logging.info('Finished monolingual dictionaries')

def check (word1, word2, l1, l2):
    "Check full words. Input: word with one tag variant (n-m). Output: full tags (n|n-m|n-m-sg)"
    word1 = l1[word1]
    word2 = l2[word2]
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

def parse_bidix (tree, lang1, lang2):
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
                    yield one_word2(p.find('l'), lang1), one_word2(p.find('r'), lang2), side
                else:
                    i = e.find('i')
                    if i:
                        yield one_word2(i, lang1), one_word2(i, lang2), side

def existance(pair, nodes):
    "Check if language pair links two languages from our list"
    if pair[0] in nodes and pair[1] in nodes: return True
    else: return False

def bidix():
    logging.info('Started bilingual dictionaries')
    if not os.path.exists('./parsed/'): os.makedirs('./parsed/')
    with open ('./tool/stats.csv','w',encoding='utf-8') as stats:
        with open('./filelist.txt', 'r', encoding = 'utf-8') as f:
            lines = f.readlines()
        for line in tqdm(lines):
            file = line.strip('\n')
            name = [l(i) for i in line.split('.')[-2].split('-')]
            nm = '-'.join(name)
            if nm in rename: 
                name = [i for i in rename[nm].split('-')]
                #l1 = import_mono(name[1])
                #l2 = import_mono(name[0])
                #print (name)
            #else:
            l1 = import_mono(name[0])
            l2 = import_mono(name[1])
            with open (file, 'r', encoding='utf-8') as d:
                with open ('./parsed/'+'-'.join(name), 'w', encoding='utf-8') as copy:
                    count = [0,0,0]
                    try:
                        tree = ET.fromstring(re.sub('\s{3,}','\t', d.read().replace('<b/>',' ').replace('<.?g>','')))
                        for word1, word2, side in parse_bidix (tree, name[0], name[1]):
                            try:
                                word1, word2 = check (word1, word2, l1, l2)
                                if not side: count[0]+=1
                                elif side == 'LR': count[1] += 1
                                elif side == 'RL': count[2] += 1
                                string = str(side) + '\t' + word1.write(mode='bi') + '\t' + word2.write(mode='bi') + '\n'
                                copy.write(string)
                            except: pass
                    except: pass
                    stats.write('\t'.join(name) + '\t'+ '\t'.join(str(i) for i in count)+'\n')
                    #print ('-'.join(name), end='\t')
    print ()
    logging.info('Finished bilingual dictionaries')

def preprocessing():
    all_languages()
    global langs
    from .langs import langs
    monodix()
    bidix()

def import_mono(lang):
    "Import monodix. Parse all lines, split them and get a dictionary of them to have all nodes in one place."
    dictionary = DiGetItem()
    with open ('./monodix/{}.dix'.format(lang), 'r', encoding='utf-16') as f:
        for line in f:
            string = line.strip('\n').split('\t')
            s = [Tags([j for j in i.split('-') if j !='']) for i in string[1].strip().split('$')]
            dictionary.add(Word(string[0], lang, s))
    return dictionary

# BUILDING

def get_relevant_languages(lang1, lang2):
    G = nx.Graph()
    with open ('./tool/stats.csv', 'r', encoding='utf-8') as f:
        for line in f:
            data = line.split('\t')
            coef = 1/log10(10+float(data[2])+0.5*float(data[3])+0.5*float(data[4]))
            if coef < 1:
                G.add_edge(data[0], data[1], weight=coef)
    result = {}
    for path in islice(nx.shortest_simple_paths(G, source=lang1, target=lang2, weight='weight'), 0, 300):
        length = sum([G[path[i]][path[i-1]]['weight'] for i in range(1, len(path))])
        for node in path:
            if node not in result:
                result[node]  = (length, path)
    config = '{}-{}-config'.format(lang1, lang2)
    with open (config,'w', encoding='utf-8') as f:
        for i in sorted(result, key=result.get):
            f.write(str(result[i][0])+'\t'+str(i)+'\t:\t'+' '.join(result[i][1])+'\n')

def load_file(lang1,lang2, n=10):
    n = int(n)
    with open ('{}-{}-config'.format(lang1, lang2),'r',encoding='utf-8') as f:
        languages = set([i.split('\t')[1].strip() for i in islice(f.readlines(), 0, n)])
    languages = languages | set([lang1,lang2])
    file = '{}-{}'.format(lang1, lang2)
    with open (file, 'w', encoding='utf-16') as f:
        for root, dirs, files in os.walk ('./parsed/'):
            for fl in files:
                pair = fl.replace('.dix','').split('-')
                if existance(pair, languages):
                    #print (pair)
                    with open (root+fl, 'r', encoding='utf-8') as d:
                        f.write(d.read())
    with open(file, 'r', encoding='utf-16') as f:
        text = f.read()
    text = text.encode('utf-8')
    text = text.decode('utf-8')
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)

def parse_line(line):
    side, lang1, lemma1, tags1, lang2, lemma2, tags2 = line.strip('\n').split('\t')
    tags1 = [Tags(i.split('-')) for i in tags1.split('$')]
    tags2 = [Tags(i.split('-')) for i in tags2.split('$')]
    return side, Word(lemma1, lang1, tags1), Word(lemma2, lang2, tags2)

def built_from_file(file):
    G = nx.DiGraph()
    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            side, word1, word2 = parse_line(line)
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

def check_graph(lang1, lang2, n=10):
    G = nx.Graph()
    with open ('./tool/stats.csv', 'r', encoding='utf-8') as f:
        for line in f:
            data = line.split('\t')
            coef = 1/log10(10+float(data[2])+0.5*float(data[3])+0.5*float(data[4]))
            if coef < 1:
                G.add_edge(data[0], data[1], weight=coef)
    with open ('{}-{}-config'.format(lang1, lang2),'r',encoding='utf-8') as f:
        languages = set([i.split('\t')[1].strip() for i in islice(f.readlines(), 0, n)])
    languages = languages | set([lang1,lang2])
    nx.draw_shell(G.subgraph(languages), with_labels = True, font_size = 20, node_color = 'white')

# SEARCH

def metric(G, word, translation, cutoff, mode='exp'):
    coef = 0
    if mode == 'exp':
        t = Counter([len(i) for i in nx.all_simple_paths(G, word, translation, cutoff=cutoff)])
        if mode == 'exp': 
            for i in t: 
                coef += exp(-i)*t[i]
            return coef

def _single_shortest_path_length(adj, firstlevel, cutoff, lang):
    """ Variant of NetworkX function _single_shortest_path_length"""
    seen = {}                  # level (number of hops) when seen in BFS
    level = 0                  # the current level
    nextlevel = firstlevel     # dict of nodes to check at next level
    result = []
    while nextlevel and cutoff >= level and len(result) < 10:
        thislevel = nextlevel  # advance to next level
        nextlevel = {}         # and start a new list (fringe)
        for v in thislevel:
            if v not in seen:
                seen[v] = level  # set the level of vertex v
                if v.lang == lang: result.append(v)
                else: nextlevel.update(adj[v])
        level += 1
    return result

def possible_translations(G, source, lang, cutoff=4):
    """ Variant of NetworkX function single_source_shortest_path_length"""
    if source not in G: raise nx.NodeNotFound('Source {} is not in G'.format(source))
    if cutoff is None: cutoff = float('inf')
    nextlevel = {source: 0}
    return _single_shortest_path_length(G.adj, nextlevel, cutoff, lang)

def evaluate(G, word, candidates, cutoff=4, topn=None):
    result = {}
    mean = 0
    for translation in candidates:
        result[translation] = metric(G, word, translation, cutoff=cutoff)
        mean += result[translation]
    result = [(x, result[x]) for x in sorted(result, key=result.get, reverse=True)]
    if topn: return result[:topn]
    else:
        result = result[:10]
        if len(result) < 10: 
            mean += exp(-cutoff-1)*(10-len(result))
        mean = mean / 10
        result = [x for x in result if x[1] > mean]
        return result

#def lemma_search (G, lemma, d_l1, l2, cutoff=4, topn=None):
#    lemmas = [i for i in d_l1.lemma(lemma) if i in G.nodes()]
#    results = {word:{} for word in lemmas}
#    for word in lemmas:
#        candidates = possible_translations(G, word, l2, cutoff=cutoff)
#        results[word] = evaluate(G, word, candidates, cutoff=cutoff, topn=topn)
#        del candidates
#    return results

#def print_results(results, n=7):
#    for i in results:
#        print ('\n\t\t', i)
#        for j in sorted(results[i], key=results[i].get, reverse=True)[:n]:
#            print (j, results[i][j])

#def print_lemma_results(results, n=10):
#    for i in results:
#        print ('\t\t', i)
#        for j in results[i]:
#            print ('{}\t{}'.format(j[0], j[1]))
#        print()

# EVALUATION

def node_search(G, node, lang2, cutoff=4, topn=None):
    if node not in G.nodes(): return None
    candidates = possible_translations(G, node, lang2, cutoff=cutoff)
    results = evaluate(G, node, candidates, cutoff=cutoff, topn=topn)
    return [i[0] for i in results]

def two_node_search (G, node1, node2, lang1, lang2, cutoff=4, topn=None):
    #if not topn: topn = 1000
    if (node1, node2) in G.edges(): G.remove_edge(node1, node2)
    if (node2, node1) in G.edges(): G.remove_edge(node2, node1)
    res1 = node_search(G, node1, lang2, cutoff=cutoff, topn=topn)
    res2 = node_search(G, node2, lang1, cutoff=cutoff, topn=topn)
    coefficient = 0
    if not topn: topn = 1000
    if node2 in res1: 
        pos = res1.index(node2)
        if pos < topn: coefficient += 0.5
        else: coefficient += 0.01
    if node1 in res2: 
        pos = res2.index(node1)
        if pos < topn: coefficient += 0.5
        else: coefficient += 0.01
    return coefficient

def _one_iter(lang1, lang2, G, k, l1, cutoff=4, topn=None):
    candidates = random.sample(l1, len(l1))
    pairs = []
    for i in candidates:
        if len(pairs) < 1000 and i in G.nodes():
            ne = list(G.neighbors(i))
            s = FilteredList(ne).lang(lang2)
            if len(s) == 1 and len(ne) > 1:
                ne = list(G.neighbors(s[0]))
                if len(FilteredList(ne).lang(lang1)) == 1 and len(ne)>1 and FilteredList(ne).lang(lang1)[0]==i:
                    pairs.append((i, s[0]))
        elif len(pairs) >= 1000: break
    if len(pairs) == 0: print ('no one-variant')
    pairs2 = pairs[:1000]
    result = []
    for i in tqdm(pairs): 
        result.append(two_node_search (G, i[0], i[1], lang1, lang2, cutoff=cutoff, topn=topn))
    print ('N=',len(pairs2), end='\t')
    try:
        precision = sum(1 for i in result if i == 1) / sum(1 for i in result if i > 0)
        recall = sum(1 for i in result if i == 1) / sum(1 for i in result)
        f1 = 2 * precision * recall / (precision + recall)
        print ('Precision : {}, recall : {}, f1-score : {}'.format(precision, recall, f1))
    except:
        print ('error')
    del G, pairs

def eval_loop(lang1, lang2, n=10, topn=None, n_iter=3, cutoff=4):
    n, cutoff, n_iter = int(n), int(cutoff), int(n_iter)
    if topn: topn = int(topn)
    get_relevant_languages(lang1, lang2)
    load_file(lang1, lang2, n=n)
    l1, l2 = dictionaries(lang1, lang2)
    k = len(l1)
    if k > 10000: k =10000
    elif k < 1000: return 'less than 1000'
    else: k = len(l1)
    for _ in range(n_iter):
        G = built_from_file('{}-{}'.format(lang1,lang2))
        _one_iter(lang1, lang2, G, k, l1, cutoff=cutoff, topn=topn)

def addition(lang1, lang2, n=10, cutoff=4):
    get_relevant_languages(lang1, lang2)
    load_file(lang1, lang2, n=n)
    change_encoding('{}-{}'.format(lang1,lang2))
    G = built_from_file('{}-{}'.format(lang1,lang2))
    l1, l2 = dictionaries(lang1, lang2)
    k1, k2 = [0,0,0,0], [0,0,0,0] #existant, failed, new, errors
    for node in l1:
        if node in G:
            s = FilteredList(list(G.neighbors(node))).lang(lang2)
            if not len(s):
                candidates = possible_translations(G, node, lang2, cutoff=cutoff)
                if candidates: k1[2] += 1
                else: k1[1] += 1
            else:
                k1[0] += 1
        else: k1[3] +=1
    if k1[0] > 0: c = k1[2]/k1[0]*100
    else: c = 0
    print ('{}->{}    Exist: {}, failed: {}, NEW: {} +{}%, NA: {}'.format(lang1, lang2, k1[0], k1[1], k1[2], round(c, 0), k1[3]))
    
    for node in l2:
        if node in G:
            s = FilteredList(list(G.neighbors(node))).lang(lang1)
            if not len(s):
                candidates = possible_translations(G, node, lang1, cutoff=cutoff, n=20)
                if candidates: k2[2] += 1
                else: k2[1] += 1
            else:
                k2[0] += 1
        else: k2[3] += 1
    if k2[0] > 0: c = k2[2]/k2[0]*100
    else: c = 0
    print ('{}->{}    Exist: {}, failed: {}, NEW: {} +{}%, NA: {}'.format(lang2, lang1, k2[0], k2[1], k2[2], round(c, 0), k2[3]))

def generate_example(l1, G, lang2):
    for i in l1:
        if i in G:
            ne = list(G.neighbors(i))
            s = FilteredList(ne).lang(lang2)
            if len(s) == 0:
                candidates = possible_translations(G, i, lang2, cutoff=4)
                result = evaluate(G, i, candidates, cutoff=4)
                if result: yield i, result

def get_translations(lang1, lang2, cutoff=4, topn=None):
    G = built_from_file('{}-{}'.format(lang1,lang2))
    l1, l2 = dictionaries(lang1, lang2)
    RESULT = {}
    for i in tqdm(l1):
        if i in G:
            ne = list(G.neighbors(i))
            s = FilteredList(ne).lang(lang2)
            if len(s) == 0:
                candidates = possible_translations(G, i, lang2, cutoff=4)
                result = evaluate(G, i, candidates, cutoff=4)
                if result:
                    for j in result: RESULT[(i, j[0])] = [j[1], 0]
    for i in tqdm(l2):
        if i in G:
            ne = list(G.neighbors(i))
            s = FilteredList(ne).lang(lang1)
            if len(s) == 0:
                candidates = possible_translations(G, i, lang1, cutoff=4)
                result = evaluate(G, i, candidates, cutoff=4)
                if result:
                    for j in result: 
                        if (j[0], i) in RESULT:
                            RESULT[(j[0], i)][1] = j[1]
                        else:
                            RESULT[(j[0], i)] = [0, j[1]]
    with open('{}-{}-preview'.format(lang1, lang2),'w',encoding='utf-8') as f:
        for i in sorted(RESULT):
            s = i[0].write(mode='out')+'\t'+i[1].write(mode='out')+'\t'+str(RESULT[i][0])+'\t'+str(RESULT[i][1])+'\n'
            f.write(s)

def parse_preview_line(line, lang1, lang2):
    lemma1, tags1, lemma2, tags2, n1, n2 = line.strip('\n').split('\t')
    tags1 = tags1.split('-')
    tags2 = tags2.split('-')
    side = None
    if float(n1) > 0 and float(n2) == 0: side = 'RL'
    elif float(n1) == 0 and float(n2) > 0: side == 'LR'
    return side, Word(lemma1, lang1, tags1), Word(lemma2, lang2, tags2)

def convert_to_dix(lang1, lang2):
    tree = ET.Element('section')
    with open ("{}-{}-preview".format(lang1, lang2),'r', encoding='utf-8') as inp:
        for line in inp:
            side, word1, word2 = parse_preview_line(line, lang1, lang2)
            if side: pair = ET.Element('e', {'r':side})
            else: pair = ET.Element('e')
            p = ET.SubElement(pair, 'p')
            l = ET.SubElement(p, 'l')
            r = ET.SubElement(p, 'r')
            l.text = word1.lemma
            r.text = word2.lemma
            for i in word1.s: 
                if i: l.append(ET.Element('s', {'n':i}))
            for i in word2.s: 
                if i: r.append(ET.Element('s', {'n':i}))
            tree.append(pair)
    ET.ElementTree(tree).write("{}-{}-new".format(lang1, lang2), encoding='utf-8')
    with open("{}-{}-new".format(lang1, lang2), 'r', encoding='utf-8') as f:
        xml = f.read()
    with open("{}-{}-new".format(lang1, lang2), 'w', encoding='utf-8') as f:
        f.write(xml.replace('<e','\n    <e').replace('</section>','\n</section>'))

def merge(lang1, lang2):
    with open ('{}-{}-merged'.format(lang1[0].upper(), lang2[0].upper()), 'w', encoding='utf-8') as result:
        for i in lang1:
            for j in lang2:
                with open("{}-{}-new".format(i, j), 'r', encoding='utf-8') as f:
                    text = f.read()
                    if len(i.split('_')) > 1: i = '_'.join(i.split('_')[1:])
                    if len(j.split('_')) > 1: j = '_'.join(j.split('_')[1:])    
                    text = text.replace('<e', '<e vl=\'{}\' vr=\'{}\' '.format(i, j))
                    result.write(text + '\n\n')