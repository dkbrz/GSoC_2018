from .func2 import *

def node_search(G, node, l2, cutoff, metric='exp', n=20):
    if node not in G.nodes():
        return None
    s = FilteredList(nx.single_source_shortest_path_length(G, node, cutoff=cutoff))
    results = {}
    candidates = possible_translations(G, node, l2, cutoff=cutoff, n=20)
    results = evaluation(G, node, candidates, mode=metric, cutoff=cutoff)
    return list(sorted(results, key=results.get, reverse=True))[:n]
    
def evaluate(G, pairs, l1, l2, cutoff=4, metric='exp', topn=5):
    result = []
    for i in pairs:
        result.append(two_node_search (G, i[0], i[1], l1, l2, cutoff, metric=metric, topn=topn))
    return result

def evaluation(G, word, candidates, mode='exp', cutoff=4):
    result = {}
    for translation in candidates:
        result[translation] = metric(G, word, translation, cutoff=cutoff, mode=mode)
    return result

def lemma_search (G, lemma, d_l1, l2, cutoff, n, metric='exp'):
    lemmas = [i for i in d_l1.lemma(lemma) if i in G.nodes()]
    results = {word:{} for word in lemmas}
    for word in lemmas:
        candidates = possible_translations(G, word, l2, cutoff=cutoff, n=n)
        results[word] = evaluation(G, word, candidates, mode = metric, cutoff=cutoff)
        del candidates
    return results

def metric(G, word, translation, cutoff, mode='exp'):
    coef = 0
    if mode in ('exp', 'len'):
        t = Counter([len(i) for i in nx.all_simple_paths(G, word, translation, cutoff=cutoff)])
        if mode == 'exp': 
            for i in t: 
                #coef += exp(-t[i])
                coef += exp(-i)*t[i]
            return coef
        if mode == 'len':
            for i in t: 
                coef += t[i]*i
            return coef
    if mode in ('log'):
        for path in nx.all_simple_paths(G, word, translation, cutoff=cutoff):
            for key, value in enumerate(path[1:]):
                coef -= G[path[key-1]][value]['weight']

def get_evaluation_pairs(G, dictionary, target, n=500):
    k = 4
    pairs = []
    while len(pairs) < n:
        candidates = random.sample(dictionary, k*n)
        pairs = []
        for i in candidates:
            if i in G.nodes():
                ne = list(G.neighbors(i))
                s = FilteredList(ne).lang(target)
                if len(s) == 1 and len(ne) > 1 and (s[0], i) in G.edges() and (i, s[0]) in G.edges(): 
                    pairs.append((i, s[0], n))
        print (k*n, len(pairs))
        k+=1
    return pairs[:n]

def one_iter_evaluation(lang1, lang2, G, k, l1, l2, cutoff=4):
    a = []
    candidates = random.sample(l1, k)
    pairs = []
    for i in candidates:
        if len(pairs) < 1000 and i in G.nodes():
            ne = list(G.neighbors(i))
            s = FilteredList(ne).lang(lang2)
            if len(s) == 1 and len(ne) > 1:
                pairs.append((i, s[0]))
        elif len(pairs) >= 1000:
            break
    if len(pairs) == 0:
        return 'no one-variant'
    pairs2 = pairs[:1000]
    result = evaluate(G, pairs2, lang1, lang2, 4)
    del G, l1, l2, pairs
    try:
        return sum(result)/len(pairs2)
    except:
        return 0

def loop(lang1, lang2, n=10, cutoff=4, n_iter=10):
    get_relevant_languages(lang1, lang2)
    load_file(lang1, lang2, n=n)
    change_encoding('{}-{}'.format(lang1,lang2))
    G = built_from_file('{}-{}'.format(lang1,lang2))
    l1, l2 = dictionaries(lang1, lang2)
    k = len(l1)
    if k > 10000: k =10000
    elif k < 1000: return 'less than 1000'
    else: k = len(l1)
    a = []
    #print ('+',end='\t')
    for _ in tqdm(range(n_iter)):
        a.append(one_iter_evaluation(lang1, lang2, G, k, l1, l2, cutoff=cutoff))
    print (a)
    print (st.t.interval(0.95, len(a)-1, loc=np.mean(a), scale=st.sem(a)))

def addition(lang1, lang2, n=10, cutoff=4):
    get_relevant_languages(lang1, lang2)
    load_file(lang1, lang2, n=n)
    change_encoding('{}-{}'.format(lang1,lang2))
    G = built_from_file('{}-{}'.format(lang1,lang2))
    l1, l2 = dictionaries(lang1, lang2)
    k1, k2 = [0,0,0,0], [0,0,0,0] #existant, failed, new, errors
    for node in tqdm(l1):
        if node in G:
            s = FilteredList(list(G.neighbors(node))).lang(lang2)
            if not len(s):
                candidates = possible_translations(G, node, lang2, cutoff=cutoff, n=20)
                if candidates: k1[2] += 1
                else: k1[1] += 1
            else:
                k1[0] += 1
        else: k1[3] +=1
    
    print ('Exist: {}, failed: {}, NEW: {}, errors: {}'.format(k1[0]/len(l1), k1[1]/len(l1), k1[2]/len(l1), k1[3]/len(l1)))
    
    for node in tqdm(l2):
        if node in G:
            s = FilteredList(list(G.neighbors(node))).lang(lang1)
            if not len(s):
                candidates = possible_translations(G, node, lang1, cutoff=cutoff, n=20)
                if candidates: k2[2] += 1
                else: k2[1] += 1
            else:
                k2[0] += 1
        else: k2[3] += 1
    
    print ('Exist: {}, failed: {}, NEW: {}, errors: {}'.format(k2[0]/len(l2), k2[1]/len(l2), k2[2]/len(l2), k2[3]/len(l2)))

def two_node_search (G, node1, node2, l1, l2, cutoff, metric='exp', topn=5):
    lng = 20
    if (node1, node2) in G.edges(): G.remove_edge(node1, node2)
    if (node2, node1) in G.edges(): G.remove_edge(node2, node1)
    res1 = node_search(G, node1, l2, cutoff, metric=metric)[:lng]
    res2 = node_search(G, node2, l1, cutoff, metric=metric)[:lng]
    coefficient = 0
    if node2 in res1: 
        pos = res1.index(node2)
        if pos < topn: coefficient += 0.5*(lng - pos)/lng
        else: coefficient += 0.01
    if node1 in res2: 
        pos = res2.index(node1)
        if pos < topn: coefficient += 0.5*(lng - pos)/lng
        else: coefficient += 0.01
    return coefficient

def _one_iter(lang1, lang2, G, k, l1, l2, cutoff=4, p=0.8, topn=5):
    a = []
    candidates = random.sample(l1, k)
    pairs = []
    for i in candidates:
        if len(pairs) < 1000 and i in G.nodes():
            ne = list(G.neighbors(i))
            s = FilteredList(ne).lang(lang2)
            if len(s) == 1 and len(ne) > 1:
                pairs.append((i, s[0]))
        elif len(pairs) >= 1000:
            break
    if len(pairs) == 0:
        return 'no one-variant'
    pairs2 = pairs[:1000]
    result = evaluate(G, pairs2, lang1, lang2, 4, topn=topn)
    print (len(pairs2))
    try:
        precision = sum(1 for i in result if i >= p) / sum(1 for i in result if i > 0)
        recall = sum(1 for i in result if i >= p) / sum(1 for i in result)
        f1 = 2 * precision * recall / (precision + recall)
        #logging.info ('finish evaluation')
        #print ('Precision : {}, recall : {}, f1-score : {}, \tSum : {}'.format(precision, recall, f1, sum(result)/(len(pairs2)//100)))
        print ('Precision : {}, recall : {}, f1-score : {}'.format(precision, recall, f1))
    except:
        print ('error')
    del G, l1, l2, pairs

def eval_loop(lang1, lang2, n=10, cutoff=4, n_iter=10, topn=5):
    p = (21 - topn)/20
    get_relevant_languages(lang1, lang2)
    load_file(lang1, lang2, n=n)
    change_encoding('{}-{}'.format(lang1,lang2))
    G = built_from_file('{}-{}'.format(lang1,lang2))
    l1, l2 = dictionaries(lang1, lang2)
    k = len(l1)
    if k > 10000: k =10000
    elif k < 1000: return 'less than 1000'
    a = []
    #print ('+',end='\t')
    for _ in tqdm(range(n_iter)):
        G = built_from_file('{}-{}'.format(lang1,lang2))
        _one_iter(lang1, lang2, G, k, l1, l2, cutoff=cutoff, p=p)
    #print (a)
    #print (st.t.interval(0.95, len(a)-1, loc=np.mean(a), scale=st.sem(a)))    

def addition2(lang1, lang2, n=10, cutoff=4):
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
                candidates = possible_translations(G, node, lang2, cutoff=cutoff, n=20)
                if candidates: k1[2] += 1
                else: k1[1] += 1
            else:
                k1[0] += 1
        else: k1[3] +=1
    if k1[0] > 0: c = k1[2]/k1[0]*100
    else: c = 0
    print ('{}->{}\tExist: {}, failed: {}, NEW: {} +{}%, NA: {}'.format(lang1, lang2, k1[0], k1[1], k1[2], round(c, 0), k1[3]))
    
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
    print ('{}->{}\tExist: {}, failed: {}, NEW: {} +{}%, NA: {}'.format(lang2, lang1, k2[0], k2[1], k2[2], round(c, 0), k2[3]))