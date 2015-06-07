#!/usr/bin/env python3

__author__ = 'anton'

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from subprocess import call

path = Path('corpora')

lengths = (4, 5)
to_process = []

for lang_dir in path.iterdir():
    try:
        for corpus_file in lang_dir.iterdir():
            if corpus_file.suffix == '.dx1':
                to_process.append(corpus_file)
    except NotADirectoryError:
        pass


with ProcessPoolExecutor() as executor:
    for corpus_file in to_process:
        for length in lengths:
            to_call = ['python3',
                       'morphology.py', str(corpus_file.resolve()), str(length),
                       '-o', 'results/{}_{}.txt'.format(corpus_file.stem,
                                                   length)]
            print(' '.join(to_call))
            executor.submit(call, to_call)