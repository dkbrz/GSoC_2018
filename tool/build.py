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
        elif side == 'LR':
            G.add_edge(word1, word2)
        elif side == 'RL':
            G.add_edge(word2, word1)
        else:
            print (side)
    return G

def dictionaries(lang1,lang2):
    l1 = import_mono(lang1)
    l2 = import_mono(lang2)
    l1 = SetWithFilter(l1.list+list(l1.dict.keys()))
    l2 = SetWithFilter(l2.list+list(l2.dict.keys()))
    return l1, l2
