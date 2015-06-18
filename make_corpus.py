#!/usr/bin/env python3

__author__ = 'anton'

from argparse import ArgumentParser
from collections import Counter
import re

from dx1 import write_dx1

arg_parser = ArgumentParser()
arg_parser.add_argument('file')
arg_parser.add_argument('output')
args = arg_parser.parse_args()

words_re = r'\w+'

with open(args.file) as file:
    data = file.read()

words = re.findall(words_re, data, flags=re.I|re.MULTILINE)

counter = Counter(words)
new_filename = args.output + '.dx1' if '.dx1' not in args.output else args.output
with open(new_filename, 'w') as new_file:
    write_dx1(counter, new_file, author='Anton Melnikov',
              comment="from '{}'".format(args.file))

