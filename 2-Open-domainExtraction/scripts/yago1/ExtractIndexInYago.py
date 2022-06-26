"""
    Extract indices in yago1
"""

import os

# extract index information in yago
# TODO: differ from kb to kb
def ExtractIndex(indices):
    path = "../../data/yago1/yago-1.0.0-native/facts"
    path_list = os.listdir(path)
    #print(path_list)
    for dir in path_list:
        if dir == ".DS_Store":
            continue
        # yagoMap.mapName(dir)
        dpath = os.path.join(path, dir)
        file_list = os.listdir(dpath)
       # print(file_list)
        for file in file_list:
            fpath = os.path.join(dpath, file)
            f = open(fpath, 'r')
            # print("=================")
            # print(fpath)
            for line in f.readlines():
                index, arg1, arg2, possibility = line.strip().split('\t')
                #print(index)
                indices.add(index)
        # print(len(indices))
        # print("index finish")
