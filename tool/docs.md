# Documentation

## Classes

Specific data requires non-standard data types.

**Word**

It has three main attributes:

- lemma : the word itself (e.g. 'table', 'football club')
- lang : language (e.g. 'eng', 'rus')
- s: tags (s-tags from dictinary) (e.g. 'n', 'sg', 'np')

Dialect is not included as it is quite rare at this time (specified for 3 languages (nor, por, cat) and for a couple of words in English.

String representation contains language, lemma and tags:

```
spa$jugar$[vblex_vblex-vbact]
```

- '_' different variants separator
- '-' tags separator

This example above shows that for this word there are two vriants of tags: vblex and vblex+vbact and vblex is more popular. (See section about shorten function).

Equality : language and lemma absolute match + tags match one of variants. So spa$jugar$[vblex] will be equal to that ibject above.

Less than (self, other) : if self is equal and other has more variants in tags.

Hash: string representation.

Write method: 

1. mode='mono' : lemma + tag variants (language is specified in filename) - for preprocessed monolingual dictionary
2. mode='bi' : language, lemma, tags - for preprocessed bilingual dictionary
3. mode='out': lemma + tag (1) - for preview and further converting into section for insertion in dictionary. If there are several tag variants the first one (most popular) will be chosen.


**Tags**

One set of tags (e.g. n+m+sg)

Equal : match

Less or equal : the second is not smaller than the first one, intersection = first.

Less than : the second is larger + intersection = first.

String representation : joined with '-' (e.g. 'n-m-sg')

Hash : string representation

**WordDict**

One word dictionary with tag variants (used for sorting them and combining words into multivariant tags object)

It has the only attribute lemma that contains lemma and a method with the same name that sets this attribute.

**FilteredDict**



**DiGetItem**

Word is a complex structure. Equality of objects doesn't mean that hash is the same (example in Word class). So we can't use hash to find whether we already have this word or not. Search in non-hash structures like list is inefficient.

Dictionary : words with one tag variant. Hash can be used to get a word. It returns the same word.

List : word with multiple variants. List search (check all one by one until we find the match). Returns full word (with all tags)

Methods:

- add : adds word
- __getitem__ : return word (full or the same)
- __len__ : len(dict) + len(list)

**SetWithFilter**

Methods:

- lemma : filters all Word objects with lemma matching our lemma

```
l1.lemma('mother')
```

this can return 'mother' as a verb, noun etc

- lang : same by language

**FilteredList**

All the same but with dictinary


## Loading

