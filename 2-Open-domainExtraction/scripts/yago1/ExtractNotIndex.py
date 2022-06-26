"""
This file aims to Extract ~indices
In my method on judging if a relation is reified, I store all indices into a set which can occupy nearly 15GB memory
After analyzing yago1, I find that there barely exists Integer in subject or object except for indices.
So in order to save limited memory resource, I just store integers which are not included in indices. Every time we
encounter an integer, we just need to check if it is in this set. If not, it is an index.
"""

from yago1.ExtractIndexInYago import ExtractIndex
import os

def isdigit(str):
    try:
        float(str)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(str)
        return True
    except (TypeError, ValueError):
        pass
    return False

def ExtractIntegers(integers):
    indices = set()
    ExtractIndex(indices)
    path = "../../data/yago1/yago-1.0.0-native/facts"
    dir_list = os.listdir(path)
    for dir in dir_list:
        dpath = os.path.join(path, dir)
        file_list = os.listdir(dpath)
        for file in file_list:
            fpath = os.path.join(dpath, file)
            f = open(fpath, 'r')
            for line in f.readlines():
                # print(line)
                index, arg1, arg2, possibility = line.strip().split('\t')
                if isdigit(arg1) == True:
                    if arg1 not in indices:
                        integers.add(arg1)
                        # print(arg1)
                if isdigit(arg2) == True:
                    if arg1 not in indices:
                        integers.add(arg2)
                        # print(arg2)
            f.close()
    f = open('./index', 'w')
    for integer in integers:
        f.write(integer)
        f.write('\n')
    f.close()

def ExtractIntegersFromFile(integers: set, path: str):
    f = open(path, 'r')
    for line in f.readlines():
        # print(line)
        # print(line)
        integer = line.strip().split('\n')
        integers.add(integer[0])
    f.close()

if __name__ == '__main__':
    integers = set()
    ExtractIntegers(integers)

