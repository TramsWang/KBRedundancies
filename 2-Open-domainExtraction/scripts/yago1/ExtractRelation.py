"""
This file aims to Extract relations in yago1
"""

import sys
sys.path.append("../../..")
from common.numeratedkb import KbRelation
from common.numeratedkb import NumerationMap
import os

def parseRelation():
    mpath = "../../data/yago1"
    rpath = "../../data/yago1/relations"
    path = "../../data/yago1/yago-1.0.0-native/facts"
    # indices = set()
    dir_list = os.listdir(path)
    yagoMap = NumerationMap(mpath)
    # ExtractIndex(indices)
    global index
    for dir in dir_list:
        index = yagoMap.name2Num(dir)
        print(index)
        yagoRelation = KbRelation(dir, index, 2)
        dpath = os.path.join(path, dir)
        file_list = os.listdir(dpath)
        for file in file_list:
            fpath = os.path.join(dpath, file)
            f = open(fpath, 'r')
            for line in f.readlines():
                index, arg1, arg2, possibility = line.strip().split('\t')
                amap1 = yagoMap.name2Num(arg1)
                print((arg1, arg2))
                amap2 = yagoMap.name2Num(arg2)
                print((amap1, amap2))
                yagoRelation.addRecord((amap1, amap2))
        yagoRelation.dump(rpath)


if __name__ == '__main__':
    parseRelation()

