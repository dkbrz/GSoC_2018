import sys
from tool.func import *
#from tool.evaluation import *

def translation_test (lang1, lang2, n=10):
    n = int(n)
    G = built_from_file('{}-{}'.format(lang1,lang2))
    l1, l2 = dictionaries(lang1, lang2)
    while True:
        s = input('lemma target_language topn:\t').split()
        #print (s)
        lemma, target = s[0], s[1]
        if len(s)>2: n = int(s[2])
        if s[1] == lang2:
            print_lemma_results(lemma_search (G, lemma, l1, lang2, 4, 20), n = n)
        elif s[1] == lang1:
            print_lemma_results(lemma_search (G, lemma, l2, lang1, 4, 20), n = n)

def check_addition (n=20):
    n = int(n)
    with open('./files/second.csv', 'r', encoding='utf-8') as inp:
        for line in inp.readlines()[:n]:
            data = line.split()
            if data[2] != '0' and data[2] != 0:
                addition2(data[0],data[1])
def example(lang1, lang2, n=20):
    n = int(n)
    G = built_from_file('{}-{}'.format(lang1,lang2))
    l1, l2 = dictionaries(lang1, lang2)
    for i, result in islice(generate_example(l1, G, lang2), n):
        print (i)
        for r in result:
            print ('\t', r[0], '\t', r[1])
method_name = sys.argv[1]
parameter_name = sys.argv[2:]

getattr(sys.modules[__name__], method_name)(*parameter_name)
