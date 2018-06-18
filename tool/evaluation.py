def node_search(node, l2, cutoff):
    if node not in G.nodes():
        return None
    s = FilteredList(nx.single_source_shortest_path_length(G, node, cutoff=cutoff))
    results = {}
    k = 0
    if len(s) > 100:
        s = s.lang(l2)
        if len(s) > 5 :s = s[:20]
    else:
        while k < 8:
            s = FilteredList(nx.single_source_shortest_path_length(G, node, cutoff=cutoff+k))
            s = s.lang(l2)
            if len(s) > 5:
                s = s[:20]
                break
            else: k += 1#translations(G, word, cutoff)
        for translation in s:
            t = Counter([len(i) for i in nx.all_simple_paths(G, node, translation, cutoff=cutoff+k)])
            coef = 0
            for i in t: coef += exp(-t[i])
            results[translation] = coef
    return list(sorted(results, key=results.get, reverse=True))
	
def two_node_search (G, node1, node2, l1, l2, cutoff):
    if (node1, node2) in G.edges(): G.remove_edge(node1, node2)
    if (node2, node1) in G.edges(): G.remove_edge(node2, node1)
    res1 = node_search(node1, l2, cutoff)
    res2 = node_search(node2, l1, cutoff)
    coefficient = 0
    if node2 in res1: coefficient += 0.5*(len(res1) - res1.index(node2))/len(res1)
    if node1 in res2: coefficient += 0.5*(len(res2) - res2.index(node1))/len(res2) 
    return coefficient
	
def evaluate(G, pairs, l1, l2, cutoff):
    result = []
    for i in pairs:
        result.append(two_node_search (G, i[0], i[1], l1, l2, cutoff))
    return result
	