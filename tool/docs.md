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

