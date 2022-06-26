import sys
sys.path.append("..")
from common.numeratedkb import NumerationMap
import re

"""
    yago map in memory
"""

findProperty = re.compile(r'\^\^(.*?)')

def parseTurtle(path):
    f = open(path)
    for line in f.readlines():
        if len(line.strip().split('\t')) != 4:
            print(line)
            continue
        subject, predicate, object, end = line.strip().split('\t')
        property = re.findall(findProperty, object)
        
    

def parseYago():
    mpath = "/sdb/sincKBs/KBRedundancies/2-Open-domainExtraction/data/yago2s/map"
    dpath = "/sdb/sincKBs/KBRedundancies/2-Open-domainExtraction/data/yago2s/simple-turtle/yago-2.5.3-turtle-simple.ttl"
    yagoMap = NumerationMap()
    parseTurtle(dpath)
    print("get finish!")
    yagoMap.dump(mpath)


if __name__ == '__main__':
    parseYago()

