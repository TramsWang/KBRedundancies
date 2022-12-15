import sys
sys.path.append("../..")
# from common.numeratedkb import NumeratedKb
from common.numeratedkb import NumerationMap
from yago1.ExtractNotIndex import ExtractIntegers, ExtractIntegersFromFile
from common.numeratedkb import parseRelFilePath
from common.numeratedkb import KbRelation
from time import strptime
from time import sleep
import xlwt
import psutil
import argparse
import gc
from glob import glob

def sortRelations(relation_list: list):
    sort_list = list()
    for relation_path in relation_list:
        rel_name, arity, record_cnt = parseRelFilePath(relation_path)
        sort_list.append([record_cnt, relation_path])
    sort_list.sort(reverse=True)
    relation_list.clear()
    for pair in sort_list:
        relation_list.append(pair[1])

# TODO: different kb may use different method to store type information
def getTypes(types : set, relation : KbRelation):
    # get type num
    records = relation.getRecordSet()
    for record in records:
        times = 0
        # we just need the second key
        for num in record:
            if times == 1:
                types.add(num)
            times = times + 1

def updateDegree(degrees : dict, relation : KbRelation):
    for record in relation.getRecordSet():
        for num in record:
            if degrees.get(num) is not None:
                degrees[num] = degrees[num] + 1
            else:
                degrees[num] = 1

def checkProperty(relation : KbRelation, integers : set, types : set, map: NumerationMap, index: int) -> bool:
    property = False
    for record in relation.getRecordSet():
        pos = 1
        is_date = False
        is_int = False
        is_type = False
        for num in record:
            if (pos == 1):
                pos = pos + 1
            if (pos == 2):
                object = map.num2Name(num)
                # check if is date
                is_date = isdate(object)
                # check if is int
                if(isdigit(object)):
                    if index == 1:
                        if object not in integers:
                            continue
                        else:
                            is_int = True
                    else:
                        is_int = True
                if object in types:
                    is_type = True
        if(is_date or is_int or is_type ):
            property = True
        #TODO: only check the first record, may be wrong
        break
    return property

def checkReified(relation: KbRelation, integers: set, map: NumerationMap) -> bool:
    is_reified = True
    for record in relation.getRecordSet():
        pos = 1
        for num in record:
            entity = map.num2Name(num)
            if(isdigit(entity) and entity not in integers):
                break
            else:
                if(pos != relation.getArity()):
                    pos = pos + 1
                else:
                    is_reified = False
        break
    return is_reified

def constructDict(relation: KbRelation, total_entity: set, o_to_s: dict, s_to_o: dict):
    # f = open("./test", 'w')
    for record in relation.getRecordSet():
        pos = 1
        sub = 0
        ob = 0
        for num in record:
            total_entity.add(num)
            if(pos == 1):
                sub = num
                pos = pos + 1
            else:
                ob = num
        if s_to_o.get(sub) is not None:
            # f.write(str(sub))
            # f.write(" found\n")
            arr = s_to_o.get(sub)
            arr.append(ob)
        else:
            # f.write(str(sub))
            # f.write(" not found\n")
            s_to_o[sub] = [ob]
        if o_to_s.get(ob) is not None:
            arr = o_to_s.get(ob)
            arr.append(sub)
        else:
            o_to_s[ob] = [sub]

def getMeta(name: str, path: str, indexmode: int, index: int, indexpath: str, dstpath: str):
    # new Excel
    excel = xlwt.Workbook(encoding='utf-8')
    style4 = xlwt.XFStyle()
    style4.num_format_str = "0.000E+00"
    styleComma = xlwt.XFStyle()
    styleComma.num_format_str = "#,##0"
    styleCommaWithDot = xlwt.XFStyle()
    styleCommaWithDot.num_format_str = "0.000E+00"
    # add Excel sheet2 and title info
    excelsheet = excel.add_sheet('Relations')
    excelsheet.write(0, 0, "relation")
    excelsheet.write(0, 1, "id")
    excelsheet.write(0, 2, "#inst")
    excelsheet.write(0, 3, "prop. (%)")
    excelsheet.write(0, 4, "property")
    excelsheet.write(0, 5, "reified")
    excelsheet.write(0, 6, "#ent.")
    excelsheet.write(0, 7, "#sub.")
    excelsheet.write(0, 8, "#obj.")
    excelsheet.write(0, 9, "functionality (%)")
    excelsheet.write(0, 10, "symmetry (%)")
    print(path)
    map = NumerationMap(path)
    mem = psutil.virtual_memory()
    used = mem.free / 1024 / 1024 / 1024
    print("free mem after extract map", used)
    degrees = dict()

    # get relation num
    relation_list = list()
    for rel_file_path in glob("%s/*.rel" % path):
        relation_list.append(rel_file_path)
    relation_num = len(relation_list)

    # get entity num
    entity_num = map.totalMappings() - relation_num

    # Extract indices
    integers = set()
    if index == 1:
        ExtractIntegersFromFile(integers, indexpath)
        mem = psutil.virtual_memory()
        used = mem.free / 1024 / 1024 / 1024
        print("free mem after extract index", used)

    # index is not included
    # TODO: indices may be a special character in yago1, other kb may need another method
    if index == 1:
        print(entity_num)
        for key in map._numMap:
            if isdigit(key) and key not in integers:
                entity_num = entity_num - 1
        print(entity_num)

    # extract relation metadata
    row = 0
    total_records = 0
    types = set()
    for relation_path in relation_list:
        rel_name, arity, record_cnt = parseRelFilePath(relation_path)
        num = map.name2Num(rel_name)
        total_records = total_records + record_cnt
        if rel_name == "type":
            relation = KbRelation(rel_name, num, arity, record_cnt, path)
            getTypes(types, relation)
    sortRelations(relation_list)
    for relation_path in relation_list:
        mem = psutil.virtual_memory()
        used = mem.free / 1024 / 1024 / 1024
        print("free mem before begin", used)
        rel_name, arity, record_cnt = parseRelFilePath(relation_path)
        num = map.name2Num(rel_name)
        relation = KbRelation(rel_name, num, arity, record_cnt, path)
        # update degree of entities
        updateDegree(degrees, relation)
        row = row + 1
        # write name
        excelsheet.write(row, 0, rel_name)
        # write id
        excelsheet.write(row, 1, map.name2Num(rel_name))
        # write num of instances
        excelsheet.write(row, 2, record_cnt, styleComma)
        # write propotion
        excelsheet.write(row, 3, relation.totalRecords() / total_records * 100, style4)
        # TODO:only consider type date integer, other situation is not considered
        # check if it is property
        property = checkProperty(relation, integers, types, map, index)
        if(property == True):
            excelsheet.write(row, 4, "true")
        else:
            excelsheet.write(row, 4, "false")        
        # extract reified info
        # TODO: reified num may be indetectable in some kb
        is_reified = False
        if index == 1:
            is_reified = checkReified(relation, integers, map)
        if(is_reified):
            excelsheet.write(row, 5, "true")
        else:
            excelsheet.write(row, 5, "false")
        # extract entity、subject、object、symmetricity
        total_entity = set()
        s_to_o = dict()
        o_to_s = dict()
        constructDict(relation, total_entity, o_to_s, s_to_o)
        excelsheet.write(row, 6, len(total_entity), styleComma)
        excelsheet.write(row, 7, len(s_to_o), styleComma)
        excelsheet.write(row, 8, len(o_to_s), styleComma)
        print(len(total_entity), len(s_to_o), len(o_to_s))
        print(len(s_to_o.keys()))
        print(len(o_to_s.keys()))
        symmetricity_num = 0
        for key in s_to_o:
            for ob in s_to_o[key]:
                if s_to_o.get(ob) is not None:
                    for ob1 in s_to_o[ob]:
                        if(ob1 == key):
                            symmetricity_num = symmetricity_num + 1
        excelsheet.write(row, 10, symmetricity_num / record_cnt * 100, style4)
        # calculate functionality
        functionality = len(s_to_o) / len(total_entity)
        excelsheet.write(row, 9, functionality * 100, style4)
        del relation
        gc.collect()
        sleep(3)
        mem = psutil.virtual_memory()
        used = mem.free / 1024 / 1024 / 1024
        print("free mem after begin", used)
    # add Excel sheet1 and title info
    excelsheet = excel.add_sheet('Overview')
    excelsheet.write(0, 0, "KB")
    excelsheet.write(0, 1, "#rel.")
    excelsheet.write(0, 2, "#ent.")
    excelsheet.write(0, 3, "#cls.")
    excelsheet.write(0, 4, "avg. dgr.")
    excelsheet.write(1, 0, name)
    excelsheet.write(1, 1, relation_num, styleComma)
    excelsheet.write(1, 2, entity_num, styleComma)
    excelsheet.write(1, 3, len(types), styleComma)
    total_degree = 0
    for key in degrees:
        total_degree = total_degree + degrees[key]
    avg_degree = total_degree / entity_num
    excelsheet.write(1, 4, avg_degree, styleCommaWithDot)
    excel.save(dstpath)

def isdate(datestr):
    # handle #
    strdata = ''
    for i in range(len(datestr)):
        temp = datestr[i]
        if temp == '#':
            strdata = strdata + '1'
        else:
            strdata = strdata + temp
    pattern = ('%Y-%m-%d', '%y-%m-%d')
    for i in pattern:
        try:
            ret = strptime(strdata, i)
            if ret:
                return True
        except:
            continue
    return False

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='arguments')
    parser.add_argument('--name','-n',type=str, required=True, help="the name of dataset")
    parser.add_argument('--path','-p',type=str, required=True, help='relative or absolute path of dataset (in numeratedkb pattern)')
    parser.add_argument('--index','-i',type=int, required=True, help="0: dataset not support reified, 1: dataset support reified")
    parser.add_argument('--indexmode','-m',type=int, default=0, help="index mode:0: ~index, 1: index")
    parser.add_argument('--indexpath','-ipath',type=str, help="index/~index should be prehandled and stored in a file")
    parser.add_argument('--dstpath','-dpath',type=str, help="file to store the result")
    args = parser.parse_args()
    getMeta(args.name, args.path, args.indexmode, args.index, args.indexpath, args.dstpath)
