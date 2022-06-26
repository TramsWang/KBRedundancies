
"""
    Extract map in yago1
"""

import sys
sys.path.append("../../..")
from common.numeratedkb import NumerationMap
import os

def parseYagoEntity(yagoMap: NumerationMap):
    path = "../../data/yago1/yago-1.0.0-native/entities"
    path_list = os.listdir(path)
    for file in path_list:
        pathname = os.path.join(path, file)
        f = open(pathname, 'r')
        for line in f.readlines():
            name, isConcept = line.strip().split('\t')
            yagoMap.mapName(name)
        print(yagoMap.totalMappings())
        f.close()


def parseYagoRelation(yagoMap: NumerationMap):
    path = "../../data/yago1/yago-1.0.0-native/facts"
    path_list = os.listdir(path)
    for dir in path_list:
        if dir == ".DS_Store":
            continue
        yagoMap.mapName(dir)
        dpath = os.path.join(path, dir)
        file_list = os.listdir(dpath)
        for file in file_list:
            fpath = os.path.join(dpath, file)
            f = open(fpath, 'r')
            for line in f.readlines():
                index, arg1, arg2, possibility = line.strip().split('\t')
                yagoMap.mapName(arg1)
                yagoMap.mapName(arg2)
    print(yagoMap.totalMappings())

def parseYago():
    mpath = "/sdb/sincKBs/KBRedundancies/2-Open-domainExtraction/data/yago1/map"
    yagoMap = NumerationMap()
    parseYagoEntity(yagoMap)
    parseYagoRelation(yagoMap)
    print("get finish!")
    yagoMap.dump(mpath)


if __name__ == '__main__':
    parseYago()

