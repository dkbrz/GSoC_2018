from .functions import *

def node_search(G, node, l2, cutoff, metric='exp'):
    if node not in G.nodes():
        return None
    s = FilteredList(nx.single_source_shortest_path_length(G, node, cutoff=cutoff))
    results = {}
    candidates = possible_translations(G, node, l2, cutoff=cutoff, n=20)
    results = evaluation(G, node, candidates, mode=metric, cutoff=cutoff)
    #k = 0
    #if len(s) > 100:
    #    s = s.lang(l2)
    #    if len(s) > 5 :s = s[:20]
    #else:
    #    while k < 8:
    #        s = FilteredList(nx.single_source_shortest_path_length(G, node, cutoff=cutoff+k))
    #        s = s.lang(l2)
    #        if len(s) > 5:
    #            s = s[:20]
    #            break
    #        else: k += 1#translations(G, word, cutoff)
    #    for translation in s:
    #        t = Counter([len(i) for i in nx.all_simple_paths(G, node, translation, cutoff=cutoff+k)])
    #        coef = 0
    #        for i in t: coef += exp(-t[i])
    #        results[translation] = coef
    return list(sorted(results, key=results.get, reverse=True))
    
def two_node_search (G, node1, node2, l1, l2, cutoff, metric='exp'):
    if (node1, node2) in G.edges(): G.remove_edge(node1, node2)
    if (node2, node1) in G.edges(): G.remove_edge(node2, node1)
    res1 = node_search(G, node1, l2, cutoff, metric=metric)
    res2 = node_search(G, node2, l1, cutoff, metric=metric)
    coefficient = 0
    if node2 in res1: coefficient += 0.5*(len(res1) - res1.index(node2))/len(res1)
    if node1 in res2: coefficient += 0.5*(len(res2) - res2.index(node1))/len(res2) 
    return coefficient
    
def evaluate(G, pairs, l1, l2, cutoff=4, metric='exp'):
    result = []
    for i in pairs:
        result.append(two_node_search (G, i[0], i[1], l1, l2, cutoff, metric=metric))
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