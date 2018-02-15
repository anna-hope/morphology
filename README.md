## Morph o logy

This repository hosts an algorithm that, given a plaintext word list,
attempts to split every word into morphemes (if any). 

It has no dependencies other than Python 3.4+

## Example usage

```python3 morphology.py corpora/eng/short_webster.txt 5 -o output.txt```

The output file will begin with some statistics about the identified morphemes,
and then will include every word in the word list, segmented first left-to-right,
and then right-to-left. In that way, it can potentially identify both suffixes and prefixes. 

## Theoretical background

The algorithm does so by building up a Patricia trie from the corpus,
and then selects every node in the trie that points to multiple child nodes 
as a constituent morpheme. Prefixes shorter than the given length 
(usually 4 or 5) are considered stems, and are not segmented.

The core of the algorithm was proposed by Zellig Harris, and subsequently adapted 
by John Goldsmith. Please refer to sections 3 and 3.1 of 
[this paper](https://people.cs.uchicago.edu/~jagoldsm/Papers/algorithm.pdf)
for more detailed discussion.


