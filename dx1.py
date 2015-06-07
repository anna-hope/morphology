from collections import namedtuple, Counter
from functools import reduce
from operator import add
from pathlib import Path

PhonoForm = namedtuple('PhonoForm', 'word phonemes')


def read_file(filename, casefold=True, end_boundary=''):
    file = Path(filename)
    with file.open() as data_file:
        if file.suffix == '.dx1':
            data = data_file.read()
            return read_dx1(data, casefold=casefold, end_boundary=end_boundary)
        else:
            return read_txt(data_file, casefold=casefold, end_boundary=end_boundary)


def read_dx1(data, casefold=True, phonology=False, end_boundary='') -> Counter:
    counted_words = Counter()
    for line in data.splitlines():
        if line.startswith('#'):
            # this line is a comment
            continue
        else:
            if phonology:
                split_line = line.split(maxsplit=2)
                word, count, phonemes = split_line
                phonemes = phonemes.split()
                phonemes.append(end_boundary)

                if casefold:
                    word = word.lower()
                # convert the phonemes list to a tuple to make it hashable
                phonoform = PhonoForm(word.lower(), tuple(phonemes))
                counted_words[phonoform] += words.append(phonoform)
            else:
                try:
                    split_line = line.split(maxsplit=1)
                    word, count = split_line[0].strip(), int(split_line[1].strip())
                except (ValueError, IndexError):
                    # this is probably an empty line
                    continue
                if casefold:
                    word = word.lower()
                counted_words[word + end_boundary] += count


    return counted_words


def read_txt(txt_file, casefold=True, end_boundary='') -> [str]:
    if casefold:
        return [w.lower() + end_boundary for w in txt_file.read().splitlines()]
    else:
        return txt_file.read().splitlines()

def combine_dx1(dx1_files, casefold=True, end_boundary='') -> Counter:
    corpora = (read_dx1(dx1, casefold=casefold, end_boundary=end_boundary)
                    for dx1 in dx1_files)
    combined_corpus = reduce(add, corpora)
    return combined_corpus


def write_dx1(counted_items: Counter, file: 'FileObject',
              sort='most_common', author=None, comment=None):
    if sort == 'most_common':
        counted_words = counted_items.most_common()
    elif sort == 'alpha':
        counted_words = sorted(counted_items.items(), key=lambda item: item[1])
    else:
        counted_words = counted_items.items()

    if author:
    	print('# {}'.format(author), file=file)
    if comment:
    	print('# {}'.format(comment), file=file)
    	
    for word, count in counted_words:
        print('{}\t{}'.format(word, count), file=file)
