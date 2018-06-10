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
            if isinstance(self.s[0],list):
                w = '['+'_'.join(['-'.join(i) for i in self.s])+']'
            else:
                w = '['+'-'.join(self.s)+']'
        else:
            w = '-'
        return str(self.lang)+'$'+str(self.lemma)+'$'+str(w)
    
    __repr__ = __str__
    
    def __eq__(self, other):
        return self.lemma == other.lemma and self.lang == other.lang and (self.s == other.s or other.s in self.s or self.s in other.s)
    
    def __lt__(self, other):
        if self.lang == other.lang:
            if self.lemma == other.lemma:
                s1 = set(self.s)
                s2 = set(other.s)
                if (not s1 - s2) and (s1&s2==s1) and (s2 - s1):
                    return True
                else:
                    return False
        else:
            return False
    
    def __hash__(self):
        return hash(str(self))
    
    def write(self, mode='mono'):
        if mode == 'mono':
            return self.lemma + '\t' + '$'.join([str(i) for i in self.s])
        elif mode == 'bi':
            return self.lang + '\t' +  self.lemma + '\t' + '$'.join([str(i) for i in self.s])
        
        
class Tags(list):
    def __le__(self, other):
        s1 = set(self)
        s2 = set(other)
        if not s1 - s2 and s1&s2==s1:
            return True
        else:
            return False
    
    def __lt__(self, other):
        s1 = set(self)
        s2 = set(other)
        if (not s1 - s2) and (s1&s2==s1) and (s2 - s1):
            return True
        else:
            return False
    
    def __eq__(self, other):
        if set(self) == set(other):
            return True
        else:
            return False
        
    def __str__(self):
        return '-'.join(self)
    
    __repr__ = __str__
    
    def __hash__(self):
        return hash(str(self))
    
    
class WordDict(dict):
    def lemma(self, lemma):
        self.lemma = lemma
        
class FilteredDict(dict):
    def set_lang(self, lang):
        self.lang = lang
    
    def lemma(self, lemma):
        return self[self.lang+'_'+lemma]
        
    def add(self, word):
        lemma = word.lang+'_'+word.lemma
        tags = Tags(word.s)
        if lemma in self:
            if tags in self[lemma]:
                self[lemma][tags] += 1
            else:
                self[lemma][tags] = 1
        else:
            self[lemma] = WordDict()
            self[lemma].lemma(lemma)
            self[lemma][tags] = 1
            
class DiGetItem:
    def __init__(self):
        self.list = []
        self.dict = {}
    
    def add(self, word):
        if len (word.s) > 1:
            self.list.append(word)
        else:
            self.dict[word] = word
    
    def __getitem__(self, key):
        key2 = Word(key.lemma, key.lang, [''])
        if key in self.dict:
            return self.dict[key]
        else:
            if key2 in self.dict:
                return self.dict[key2]
            try:
                key = self.list[self.list.index(key)]
                return key
            except:
                print (key)
                
class SetWithFilter(set):
    def lemma(self, value):
        return set(i for i in self if i.lemma == value)
    def lang(self, value):
        return set(i for i in self if i.lang == value)

class FilteredList(list):
    def lemma(self, value):
        return list(i for i in self if i.lemma == value)
    def lang(self, value):
        return list(i for i in self if i.lang == value)