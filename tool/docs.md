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

Recommendations for choosing best languages to include in graph.

Graph:

- nodes - languages
- edges - weighted existing bilingual dictionaries

Weights:

EdgeWeight = 1 / log10(both_sides + 0.5*LR + 0.5*RL)

In this graph we take 300 best (shortest) paths between 2 languages and those languges that occur in these paths are recommended. They are sorted in order of length of the best path in which they occur.

Example: eng-spa

```
0.22082497988083025	eng	:	eng spa
0.22082497988083025	spa	:	eng spa
0.4250627830992572	cat	:	eng cat spa
0.44444829199452307	epo	:	eng epo spa
...
0.6661607856269738	nor	:	eng nor ita spa
0.66687498614133	arg	:	eng cat arg spa
...
1.0200843703377707	sme	:	eng fin sme eus spa
1.0451794809559942	cos	:	eng ita cos spa
1.0551281116166376	dan	:	eng nor dan deu spa
```

**load_file**

It takes top-N languages from configuration file and merges bilingual dictionaries (preprocessed) with both languages in this short list.

**parse_line**

It parses line in loading file (with edges) and returns side (LR, RL, both) and two Word objects.

**built_from_file**

This function returns a graph based on loading file (this graph will be used in further ditionary enrichment)

**dictionaries**

Returns two dictionaries (from pair we want to enrich) as SetWithFilter. So we can go through all words and create suggestions about possible translations.

**check_graph**

Probably for ipynb. Shows graph of languages that will be included in graph (languages and bilingual dictionaries).

## Search

**metric**

Evaluates translation (word+translation).

coefficient = sum(exp^(-i)), i - length of path from all simple paths between word and translation with set cutoff.

**_single_shortest_path_length**

Variant of NetworkX function _single_shortest_path_length

Yields all possible translations with cutoff. 

Cutoff: n steps from source node + stops when target language node occur or there are more then 10 variants (less then 10 + next level(cutoff))

**possible_translations**

Wrapper for previous _single_shortest_path_length function.

**evaluate**

Evaluates candidates from possible translations.

Options:

1. topn - returns top-N candidates
2. "auto" - relevant candidates

"auto"

If there are 10+ candidates returns those that have coefficient more than average. Usually there are top variants and other variants have very low coefficient. So it filters relevant candidates based on particular case coefficients

If there are less than 10 candidates, adds coefficients with minimal coefficient to get more reliable data. And then it returns same top candidates.

## Evaluation

**node_search**

Returns translations (without coefficients) for a particular node using possible_translations and evaluate functions.

**two_node_search**

Evaluation of pair of real translations.

LR: if the right one is in translations and index < topn +0.5, index >= topn +0.01

The same for RL side.

1: both sides right

0: both sides wrong

(0,1): there is some truth but not perfect translation

**_one_iter**

One iteration of evaluation.

1. Select up to 1000 random mutually unambiguous pairs.
2. Evaluate with two_node_search
3. Calculate precision, recall, f1

```
# all perfect to perfect+non-zero
precision = sum(1 for i in result if i == 1) / sum(1 for i in result if i > 0)
# all perfect to all
recall = sum(1 for i in result if i == 1) / sum(1 for i in result)
# usual f1
f1 = 2 * precision * recall / (precision + recall)
``` 

**eval_loop**

Calculates precision, recall and f1 for language pair.


**addition**

How many entries we can add LR and RL side (both only after merging - in a real file)


**get_translations**

1. Loading dictionaries
2. Building graph
3. Searching for non-existent translations
4. Writing preview file (for human assessment)

**parse_preview_line**

Subfunction to the one below. It parses a line in a preview file and returns side + 2 Word objects

**convert_to_dix**

Converting preview file into section for usual .dix file.

**merge**

Merging files with different dialects. All languages or dialects are written in vr and vl tags.