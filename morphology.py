#!/usr/bin/env python3.4

from argparse import ArgumentParser
from collections import OrderedDict, deque, Counter
from itertools import chain
import pprint
from statistics import mean, pstdev
import sys

import dx1


class Trie:

    __slots__ = ['root']

    def __init__(self):
        self.root = {}

    def __repr__(self):
        '''pretty print the trie'''
        return 'Trie({})'.format(pprint.pformat(self.root))

    def __getitem__(self, string):
        '''gets the final node of a word (if the trie has the word)
        e.g. "get" would return the node after "t"'''
        current_node = self.root
        for char in string:
            if char in current_node.keys():
                current_node = current_node[char]
            else:
                raise KeyError(string)
        return current_node

    def __contains__(self, string):
        '''allows to check if the trie contains a word'''
        try:
            current_node = self[string]
        except KeyError:
            return False
        # check if the word is ended
        return None in current_node.keys()

    def __iter__(self):
        return iter(self.root.items())

    def add(self, string):
        current_node = self.root
        for char in string:
            if char in current_node.keys():

                # go down the tree
                current_node = current_node[char]
            else:

                # create a new node
                current_node[char] = {}
                current_node = current_node[char]
        # end the word
        current_node[None] = None

    def starts_with(self, prefix, current_node=None):
        '''yields all words which start with a given prefix'''
        if not current_node:
            try:
                current_node = self[prefix]
            except KeyError:
                # the trie contains nothing with this prefix
                return

        for key in current_node.keys():
            if key is None:
                # we have reached the end of the word
                yield prefix
            else:
                # we have not reached the end
                # go further down the tree and yield the other words
                # adding the key to the prefix
                yield from self.starts_with(prefix + key)

    def num_words(self, current_node=None):
        num = 0
        if not current_node:
            current_node = self.root
        keys = current_node.keys()

        for key in keys:
            if key is None:
                num += 1
            else:
                num += self.num_words(current_node[key])

        return num


class MorphemeTrie(Trie):
    def __init__(self, letter_trie, reverse=False):
        super().__init__()
        self.letter_trie = letter_trie
        self.reverse = reverse
        self._split_chunks()

    def __str__(self):
        '''prints a detailed output of every word split into morphemes'''
        items = []
        for key in self.root.keys():
            branches = self.starts_with([key])
            for branch in branches:
                if self.reverse:
                    items.append('    '.join(m[::-1] for m in reversed(branch)))
                else:
                    items.append('    '.join(branch))
        string = '\n'.join(items)
        return string


    def _split_chunks(self, current_node=None,
                      chunks=None, current_chunk=''):
        if not current_node:
            current_node = self.letter_trie.root
        if not chunks:
            chunks = deque()

        if len(current_node.keys()) is 1:
            key = deque(current_node.keys())[0]

            # not the end of a word
            if key:
                current_chunk += key
                new_node = current_node[key]
                self._split_chunks(new_node, chunks, current_chunk)

            # the end of a word (final node)
            else:
                # add the chunks to chunk trie
                chunks.append(current_chunk)
                self.add(chunks)

                # remove the last morpheme (we won't need it)
                chunks.pop()
                return
        else:
            if current_chunk != '':
                chunks.append(current_chunk)

            for key in current_node.keys():

                #
                if key:
                    current_chunk = key
                    new_node = current_node[key]
                    self._split_chunks(new_node, chunks, current_chunk)

                # the end of a word (but there is a longer word to follow)
                else:
                    self.add(chunks)

            # we won't need the last chunk for other branches
            try:
                chunks.pop()
            except IndexError:
                # the current chunk is '', so it wasn't added to the deque
                pass

    @property
    def min_stem_length(self) -> int:
        return len(min(self.root.keys(), key=len))

    def starts_with(self, morphemes):
        try:
            current_node = self[morphemes]
        except KeyError:
            return

        for key in current_node.keys():
            if key is None:
                yield morphemes
            else:
                yield from self.starts_with(morphemes + [key])

    def get_morphemes(self, word):
        n = self.min_stem_length
        stem = word[:n]
        while not stem in self.root.keys():
            try:
                # try finding the stem in the trie's keys
                stem += word[n]
                n += 1
            except IndexError:
                # this word is not in the trie
                return None

        for candidate in self.starts_with([stem]):
            if ''.join(candidate) == word:
                return list(candidate)

    @property
    def morphemes(self):
        for stem in self.root.keys():
            yield from self.starts_with([stem])

    def contains_morpheme(self, morpheme: str, current_node: dict=None) -> bool:
        """
        :param morpheme: morpheme to check
        :param current_node: the current node of the search
        :return: whether the MorphemeTrie contains a morpheme
        """
        if not current_node:
            current_node = self.root

        for key in current_node.keys():
            if morpheme == key:
                return True
            else:
                return self.contains_morpheme(morpheme, current_node[key])

        return False


    def morphemes_per_word(self, current_node=None, level=0):
        if not current_node:
            current_node = self.root
        for key in current_node.keys():
            if key is None:
                yield level
            else:
                yield from self.morphemes_per_word(current_node[key],
                                                   level + 1)

    def morpheme_ratio(self):
        morphemes_per_word = self.morphemes_per_word()
        ratio = mean(morphemes_per_word)
        return ratio

def make_tries(words, k) -> (MorphemeTrie, MorphemeTrie):
    trie = Trie()
    reverse_trie = Trie()

    for word in words:
        trie.add([word[:k]] + list(word[k:]))
        reversed_word = word[::-1]
        reverse_trie.add([reversed_word[:k]] + list(reversed_word[k:]))

    chunk_trie_ltr = MorphemeTrie(trie)
    chunk_trie_rtl = MorphemeTrie(reverse_trie, reverse=True)
    return chunk_trie_ltr, chunk_trie_rtl


def morpheme_ratio(trie: MorphemeTrie, reverse_trie: MorphemeTrie) -> (float, float, float):
    """calculates the average of how many morphemes there are in each word"""
    trie_ratio = trie.morpheme_ratio()
    reverse_trie_ratio = reverse_trie.morpheme_ratio()
    mean_ratio = mean((trie_ratio, reverse_trie_ratio))
    return trie_ratio, reverse_trie_ratio, mean_ratio

def morpheme_stdev(trie: MorphemeTrie, reverse_trie: MorphemeTrie) -> (float, float, float):
    trie_mpr, reverse_trie_mpr = (list(trie.morphemes_per_word()),
                                    list(reverse_trie.morphemes_per_word()))
    stdev_trie = pstdev(trie_mpr)
    stdev_reverse_trie = pstdev(reverse_trie_mpr)
    stdev_combined = pstdev(trie_mpr + reverse_trie_mpr)
    return stdev_trie, stdev_reverse_trie, stdev_combined

def get_morpheme_occurrence(trie: MorphemeTrie, reverse_trie: MorphemeTrie) -> (float,):
    """calculates data on how often each morpheme occurs in the corpus"""
    morphemes_ltr = Counter(chain.from_iterable(trie.morphemes))
    morphemes_rtl = Counter(chain.from_iterable(reverse_trie.morphemes))
    morpheme_occurrences_ltr = morphemes_ltr.values()
    morpheme_occurrences_rtl = morphemes_rtl.values()

    mean_occurrence_ltr = mean(morpheme_occurrences_ltr)
    mean_occurrence_rtl = mean(morpheme_occurrences_rtl)

    stdev_morphemes_ltr = pstdev(morpheme_occurrences_ltr, mu=mean_occurrence_ltr)
    stdev_morphemes_rtl = pstdev(morpheme_occurrences_rtl, mu=mean_occurrence_rtl)

    occurrence_data = ((mean_occurrence_ltr, mean_occurrence_rtl),
                        (stdev_morphemes_ltr, stdev_morphemes_rtl))
    return occurrence_data


def produce_output(chunk_trie_ltr: MorphemeTrie, chunk_trie_rtl: MorphemeTrie, file):
    morph_ratio, rev_morph_ratio, combined_ratio = morpheme_ratio(chunk_trie_ltr,
                                                                  chunk_trie_rtl)
    stdev_trie, stdev_reverse_trie, stdev_combined = morpheme_stdev(chunk_trie_ltr,
                                                                    chunk_trie_rtl)

    occurrence_data = get_morpheme_occurrence(chunk_trie_ltr, chunk_trie_rtl)
    avg_morphs_ltr, avg_morphs_rtl = occurrence_data[0]
    stdev_morphemes_ltr, stdev_morphemes_rtl = occurrence_data[1]

    print('Morphemes per word:', file=file)
    print('left-to-right: {:.2f}'.format(morph_ratio), file=file)
    print('right-to-left: {:.2f}'.format(rev_morph_ratio), file=file)
    print('combined morpheme-per-word ratio: {:.2f}\n'.format(combined_ratio), file=file)

    print('Standard deviation:', file=file)
    print('left-to-right: {:.2f}'.format(stdev_trie), file=file)
    print('right-to-left: {:.2f}'.format(stdev_reverse_trie),file=file)
    print('combined: {:.2f}\n'.format(stdev_combined), file=file)
    print('coefficient of variation (stdev / morpheme ratio): {:.2f}\n'.
        format(stdev_combined/combined_ratio), file=file)

    print('each morpheme occurs on average:', file=file)
    print('left-to-right: {:.2f} times'.format(avg_morphs_ltr), file=file)
    print('right-to-left: {:.2f} times\n'.format(avg_morphs_rtl), file=file)

    print('Standard deviation of the occurrence of individual morphemes:', file=file)
    print('left-to-right: {:.2f}'.format(stdev_morphemes_ltr), file=file)
    print('right-to-left: {:.2f}'.format(stdev_morphemes_rtl), file=file)

    print('\ncoefficient of variation:', file=file)
    print('left-to-right: {:.2f}'.format(stdev_morphemes_ltr/avg_morphs_ltr),
          file=file)
    print('right-to-left: {:.2f}'.format(stdev_morphemes_rtl/avg_morphs_rtl),
          file=file)

    print('\n\n', file=file)
    print('Left-to-right:', file=file)
    print('{}\n\n\n'.format(chunk_trie_ltr), file=file)
    print('right-to-left:', file=file)
    print(chunk_trie_rtl, file=file)

def run():
    k = args.minlength
    words = sorted(word.lower() for word in dx1.read_file(args.file)
                   if len(word) >= k)
    chunk_trie_ltr, chunk_trie_rtl = make_tries(words, k)

    if args.output_file:
        with open(args.output_file, 'w') as output_file:
            produce_output(chunk_trie_ltr, chunk_trie_rtl, output_file)
    else:
        produce_output(chunk_trie_ltr, chunk_trie_rtl, sys.stdout)

if __name__ == '__main__':
    argparser = ArgumentParser()
    argparser.add_argument('file', help='the corpus file')
    argparser.add_argument('minlength', type=int, help='minimal stem length')
    argparser.add_argument('-o', '--output_file', help='print output to a file')
    args = argparser.parse_args()
    run()
