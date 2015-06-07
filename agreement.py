#!/usr/bin/env python3

__author__ = 'anton'

from argparse import ArgumentParser
from collections import Counter, defaultdict
from copy import deepcopy
from functools import partial
from itertools import combinations, filterfalse
from pathlib import Path
from random import randint
import re
from statistics import mean


from morphology import Trie



class EndingTrie(Trie):

    __slots__ = ['root', 'words', 'endings']

    def __init__(self):
        super().__init__()
        self.words = Counter()
        self.endings = Counter()


    def __getitem__(self, string):
        '''gets the final node of a word (if the trie has the word)
        e.g. "get" would return the node after "t"'''
        if isinstance(string, str):
            return super().__getitem__(string)
        else:
            current_node = self.root
            for part in string:
                current_node = current_node[part]
            return current_node

    def add_word(self, word: str):
        self.words[word] += 1

    def starts_with(self, prefix, current_node=None):
        if isinstance(prefix, str):
            yield from super().starts_with(prefix, current_node)
        else:
            try:
                current_node = self[prefix]
            except KeyError:
                return
            for key in current_node:
                if key is None:
                    yield prefix
                else:
                    yield from self.starts_with(prefix + [key])


    def num_successors(self, ending) -> int:
        return len(list(self.starts_with(ending)))

    @property
    def all_successor_nums(self):
        for key in self.root:
            if len(key) > 1:
                key = [key]
            yield self.num_successors(key)

    @property
    def total_num_successors(self):
        return sum(self.all_successor_nums)

    @property
    def avg_num_successors(self):
        return mean(self.all_successor_nums)

    def filter_rare_endings(self):
        """removes all endings which are followed by too few words"""
        avg_successors = self.avg_num_successors
        root_copy = deepcopy(self.root)
        for key in root_copy:
            if self.num_successors(key) < avg_successors:
                del self.root[key]


    def collapse_endings(self):
        self.filter_rare_endings()

        keep_going = True

        while keep_going:
            root_copy = deepcopy(self.root)
            # set the iteration to stop by default (if no endings could be optimised)
            keep_going = False

            # iterate over the last chunk of every word (starting at -1)
            for ending in root_copy:

                # iterate over the following chunk of every word (-2)
                for next_ending in root_copy[ending]:

                    # check that it's not None
                    if next_ending:
                        # combine the current chunk with the next chunk in the trie

                        new_ending = ending+next_ending

                        if len(ending) > 1:
                            # we need to search by the whole chunk
                            num_successors = self.num_successors([ending, next_ending])
                        else:
                            num_successors = self.num_successors(new_ending)

                        # if this new chunk has more words following it than the average
                        if num_successors > self.avg_num_successors:

                            # turn the current chunk into the new chunk
                            self.root[new_ending] = deepcopy(self.root[ending][next_ending])
                            # delete the tree it contains (effectively moving it down)
                            del self.root[ending][next_ending]
                            # and reset keep_going to true because there still might be endings to optimise
                            keep_going = True

        # now throw out the endings which are not followed by many chunks
        root_copy = deepcopy(self.root)
        avg_successors = self.avg_num_successors

        for ending in root_copy.keys():
            if self.num_successors([ending]) < avg_successors:
                del self.root[ending]

        endings = Counter()
        sorted_endings = sorted(self.root.keys(), key=len, reverse=True)

        for ending in sorted_endings:
            for word, count in deepcopy(self.words).items():
                if word[:len(ending)] == ending:
                    endings[ending] += count
                    del self.words[word]

        self.endings = endings



class StemEndingCounter:
    def __init__(self):
        self.words_endings = defaultdict(EndingTrie)
        self.filtered_endings = None

    def __getitem__(self, item) -> EndingTrie:
        word = item
        counted_stem = self.words_endings[word]
        return counted_stem

    def __repr__(self):
        return repr(self.words_endings)

    def add(self, word, other_word):
        self.words_endings[word].add(''.join(reversed(other_word)))
        self.words_endings[word].add_word(''.join(reversed(other_word)))

        self.words_endings[other_word].add(''.join(reversed(word)))
        self.words_endings[other_word].add_word(''.join(reversed(word)))

    @property
    def stems(self):
        return self.words_endings.keys()

    def collapse_endings(self, print_progress=True):
        len_values = len(self.words_endings.values())
        for n, (word, endings_trie) in enumerate(self.words_endings.items()):
            if print_progress:
                print('{:.2f}%'.format(n / len_values * 100))
            endings_trie.collapse_endings()
            self.words_endings[word] = endings_trie

    def filter_endings(self, cutoff=0.012, recalculate=False) -> dict:
        '''lazy function'''
        if self.filtered_endings and not recalculate:
            return self.filtered_endings

        ordered_endings = sorted(self.words_endings.items(),
                                 key=lambda item: sum(item[1].endings.values()),
                                 reverse=True)

        endings = deepcopy(self.words_endings)

        len_values = len(self.words_endings.values())
        for n, (word, _) in enumerate(ordered_endings):
            if n / len_values > cutoff:
                del endings[word]

        self.filtered_endings = endings
        return endings

    # def add_up_mirror_endings(self):
    #     filtered_endings = self.filter_endings()
    #
    #     joined_endings = combinations(filtered_endings.items(),
    #                                   self.words_endings.items())
    #     for (word, endings_trie), (word2, endings_trie2) in joined_endings:
    #         for
    #
    #     for word, endings_trie in filtered_endings.items():
    #         for ending, _ in endings_trie.endings.most_common(5):
    #             for endings_trie2 in self.words_endings.values():
    #                 if ending in endings_trie2.endings:
    #                     ending_counter[ending] += 1

    def optimize_words(self, cutoff=0.012) -> list:


        filtered_endings = self.filter_endings()
        optimized_words = []
        for word, endings_trie in filtered_endings.items():

            total_occurrences = sum(endings_trie.endings.values())
            top_occurrence = endings_trie.endings.most_common(1)[0][1]
            top_vs_all = top_occurrence / total_occurrences
            unreversed_endings = [(''.join(reversed(ending)), occurrence)
                                  for ending, occurrence
                                  in endings_trie.endings.most_common(3)]
            optimized_words.append((word,
                                 unreversed_endings,
                                 top_vs_all,
                                 total_occurrences))

        return optimized_words



    def most_common(self, n=None):

        optimized_words = self.optimize_words()
        sorted_words = sorted(optimized_words, key=lambda item: item[2], reverse=True)

        return sorted_words


    def prioritize_endings(self):
        # calculate the sureness (i.e. how strongly each word associates with its top endings)
        association_scores = []
        association_strengths = {}
        ending_counter = Counter()

        filtered_endings = self.filter_endings()
        for word, endings_trie in filtered_endings.items():
            try:
                (ending1, score1), (ending2, score2) = endings_trie.endings.most_common(2)
            except ValueError:
                # there is only one top ending
                association_strengths[word] = 1
                continue

            association_strength = 1 / (score1 / score2)
            association_scores.append(association_strength)
            association_strengths[word] = association_strength

            for ending, _ in endings_trie.endings.most_common(5):
                for endings_trie2 in self.words_endings.values():
                    if ending in endings_trie2.endings:
                        ending_counter[ending] += 1

        avg_association_strength = mean(association_strengths.values())

        sum_all_endings = sum(ending_counter.values())
        uniqueness_scores = {ending: 1 - score / sum_all_endings
                             for ending, score in ending_counter.items()}

        # prioritize each ending based on its uniqueness score
        prioritized_endings = {}
        for word, endings_trie in filtered_endings.items():
            if association_strengths[word] > avg_association_strength:
                # the force is strong in this one
                endings_word = {ending: count
                                for ending, count
                                in endings_trie.endings.most_common(3)}
            else:
                endings_word = {ending: uniqueness_scores[ending]
                                for ending, _
                                in endings_trie.endings.most_common(3)}
            prioritized_endings[word] = endings_word

        return prioritized_endings

    def most_common_unique(self):
        prioritized_endings = self.prioritize_endings()
        sorted_words = []
        for word, ending_scores in prioritized_endings.items():
            unreversed_endings = [(''.join(reversed(ending)), score)
                                  for ending, score
                                  in sorted(ending_scores.items(),
                                            key=lambda item: item[1],
                                            reverse=True)]
            sorted_words.append((word,
                                 unreversed_endings))

        sorted_words = sorted(sorted_words, key=lambda item: item[1], reverse=True)
        return sorted_words


def group_data(lines):
    stem_ending_counter = StemEndingCounter()
    for line in lines:
        word_pairs = combinations(line, 2)
        for word, other_word in word_pairs:
            stem_ending_counter.add(word, other_word)

    return stem_ending_counter

def write_results(grouped_data, stream):
    for word, endings, preference, occurrence in grouped_data.most_common():
        print(word, end='\t', file=stream)
        print(*endings, end='\t', file=stream)
        print('association preference: {:.2f}%'.format(preference * 100), end='\t', file=stream)
        print('co-occurrence: {}'.format(occurrence), file=stream)

    print('\n', '-'*10, '\n', file=stream)

    for item in grouped_data.most_common_unique():
        print(*item, file=stream)

def filter_rare_words(words) -> filter:
    avg_occurrence = mean(words.count(w) for w in words)
    only_common = filter(lambda x: words.count(x) > avg_occurrence, words)
    return only_common


def run(filename, linelength=None):
    with open(filename) as data_file:
        data = data_file.read()

    word_re = re.compile(r'\w+')
    words = [word.casefold() for word in word_re.findall(data)]

    lines = []
    current_line = []

    if linelength:
        linelength = lambda: linelength
    else:
        linelength = partial(randint, 5, 15)

    for n, word in enumerate(words):
        # split the words into 'sentences' arbitrarily
        # NOTE: this number **significantly** affects the outcome
        if n % linelength() == 0:
            lines.append(current_line)
            current_line = []
        current_line.append(word)

    grouped_data = group_data(lines)
    grouped_data.collapse_endings()

    new_filename = Path('results_{}.txt'.format(Path(filename).stem))
    with new_filename.open('w') as new_file:
        write_results(grouped_data, new_file)

if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('file')
    arg_parser.add_argument('-l', '--linelength', type=int, default=0,
                            help='line length to take; defaults to random(10, 20)')
    args = arg_parser.parse_args()
    run(args.file, args.linelength)

