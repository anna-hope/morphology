#!/usr/bin/env python3

__author__ = 'anton'

from argparse import ArgumentParser
from collections import Counter, defaultdict
from itertools import chain
from pprint import pprint

from dx1 import read_dx1

def run(filename, ending):
    with open(filename) as file:
        words = read_dx1(file.read(), True)

    words_with_ending = [w for w in words
                         if w.endswith(ending) and not w == ending]
    words_without = sorted(w[:-len(ending)] for w in words_with_ending)

    matched_words = defaultdict(set)
    for word in words:
        if word:
            for word_without in words_without:
                if word.startswith(word_without) and not word.endswith(ending):
                    matched_words[word_without].add(word)

    counted_words_ending = {w: words[w]
                            for w in words_with_ending}

    counted_matches = Counter()
    for word in chain.from_iterable(matched_words.values()):
        counted_matches[word] += words[word]

    total_words = sum(words.values())
    total_words_ending = sum(counted_words_ending.values())
    total_matched = sum(counted_matches.values())

    with open('words_without_{}.txt'.format(ending), 'w') as results_file:
        print('length of corpus: {} words'.format(total_words), file=results_file)
        print('words that end with {}: {} ({:.2f}% of total)'.format(
            ending, total_words_ending,
                    total_words_ending/total_words * 100),
            file=results_file)

        print('matching words without {}: {} ({:.2f}% of total)'.format(
            ending, total_matched, total_matched / total_words * 100
        ), file=results_file)
        pprint(matched_words, stream=results_file)


if __name__ == '__main__':
    argparser = ArgumentParser()
    argparser.add_argument('file', help='the corpus file')
    argparser.add_argument('ending')
    args = argparser.parse_args()
    print('working...')
    run(args.file, args.ending)