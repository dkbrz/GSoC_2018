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

All the same but with dictionary


## Loading

**set_github_user**

Saves username and password so Github Python library can work (to download all bilingual dictionaries)


**l**

Language code converter

This function takes dictionary from data file where there are 2-letter code and converts it into 3-letter code. Also there are some dialect forms for convertation.

**repo_names**

Takes repositories from Apertium Github that match language pair name pattern.

```
'apertium-[a-z]{2,3}(_[a-zA-Z]{2,3})?-[a-z]{2,3}(_[a-zA-Z]{2,3})?'
```

**bidix_url**

Find raw url for bidix. Sorting in order to find bidix faster as it is one of the longest filename in repository.

In list of files sorted by length it checks whether filename matches bilingual dictionary name pattern until one is found or there are no more elements in file list.

**download**

This function combines previous functions.

1. Load username and password from secure file.
2. Create a folder for dictionaries.
3. Save all bilingual dictionaries from Apertium Github.

**list_files**

Creates file list that contains all file names of dictionaries that need to be considered for preprocessing (some can be excluded to avoid unnecessary preprocessing that is quite slow).

Option 1: downloaded dictionaries + no dialects - only list of files in 'dictionaries' folder

Option 2: downloaded dictionaries + dialects - list of splitted files with dialects + ordinary dictionaries

Option 3: user dictionaries in path + no dialects

Option 4: user dictionaries + dialects - list of files and splitted files in 'dictionaries' folder (to avoid damage to real files)

**split_dialects**

Checks all files in folder or path (if path) and splits them on different dictionaries for each dialect combination (e.g. nor-nno-nob)

## Preprocessing

**all_languages**

Set of all languages in bilingual dictionaries. This set is used for monolingual dictionaries.

**one_language_dict**

It gathers all words in all bilingual dictionaries that contain this particular language.

**shorten**

One of the most important functions. It combines different tags for words into one object if they don't contradict. Priority to most frequent ones.

If we have 5 dictionaries with 'стол' as n-m and 1 with n-m-sg than tag sequence will be [n-m_n-m-sg] because n-m is more likely to be actual and enough while automatic tag selection. Moreover, when we have contradicting tags like n-f-sg and n-m we have to decide to which one we can write a sole 'n' in some dictionary.

**one_word**

Parsing one word ('l' or 'r' in bilingual dictionary). Convert it into Word object.

**parse_one**

Yields all words (Word objects) from one bilingual dictionary.

**dictionary_to_nodes**

Process all word in dictinary (shorten tags and yield all variants)

**monodix**

Creates artificially created monolingual dictionaries with words that have all tag variants and ready to be used in bilingual dictionary parsing.

For each language in list of languages this function creates a dictionary.

**check**

This function gets word with tags from real bilingual dictionary and creates an object (with multiple tags) that matches this word (node for graph)

**one_word2**

Parsing words (modification of one_word)

**parse_bidix**

Bilingual dictionary parsing. Creates a file that contains all word pairs from original dictionary but in proper form for a future graph.

**existance**

Checks language nodes in language graph (nodes - languages, edges - existing bilingual dictionaries)

**bidix**

Parsing bilingual dictionaries from file list. Creates all preprocessed copies of these dictionaries.

1. Creates 'parsed' folder for these dictionaries.
2. Creates 'stats' file that will contain information about the size of all bilingual dictionaries (this will be used to define valuable dictionaries and languages for a graph).
3. Converts original dictinary into parsed copy.
4. Counts both, RL and LR words.


**preprocessing**

Combination of previous functions: all_languages, monodix and bidix.

**import mono**

Reads artificial monodix and creates a dictionary with all word in this language.

## Building graph

**get_relevant_languages**

