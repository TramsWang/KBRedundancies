import sys
sys.path.append("../../..")
# from common.numeratedkb import NumeratedKb
from common.numeratedkb import NumerationMap
from ExtractNotIndex import ExtractIntegers
from common.numeratedkb import parseRelFilePath
from common.numeratedkb import KbRelation
from time import strptime
from time import sleep
import xlwt
import psutil
import os
import gc

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

def checkProperty(relation : KbRelation, integers : set, types : set, map: NumerationMap) -> bool:
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
                    if object not in integers:
                        continue
                    else:
                        is_int = True
                if object in types:
                    is_type = True
        if(is_date or is_int or is_type ):
            property = True
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
            arr = s_to_o.get(sub)
            arr.append(ob)
        else:
            s_to_o[num] = [ob]
        if o_to_s.get(ob) is not None:
            arr = o_to_s.get(ob)
            arr.append(sub)
        else:
            o_to_s[num] = [sub]

def getMeta():
    # new Excel
    excel = xlwt.Workbook(encoding='utf-8')
    # add Excel sheet2 and title info
    excelsheet = excel.add_sheet('relations')
    excelsheet.write(0, 0, "relation")
    excelsheet.write(0, 1, "id")
    excelsheet.write(0, 2, "instances")
    excelsheet.write(0, 3, "propotion")
    excelsheet.write(0, 4, "property")
    excelsheet.write(0, 5, "reified")
    excelsheet.write(0, 6, "entites")
    excelsheet.write(0, 7, "subjects")
    excelsheet.write(0, 8, "objects")
    excelsheet.write(0, 9, "functionality")
    excelsheet.write(0, 10, "symmetricity")
    map = NumerationMap("../../data/yago1")
    mem = psutil.virtual_memory()
    used = mem.free / 1024 / 1024 / 1024
    print("free mem after extract map", used)
    degrees = dict()

    # get relation num
    relation_list = os.listdir("../../data/yago1/relations")
    relation_num = len(relation_list)

    # get entity num
    entity_num = map.totalMappings() - relation_num
    integers = set()
    ExtractIntegers(integers)
    mem = psutil.virtual_memory()
    used = mem.free / 1024 / 1024 / 1024
    print("free mem after extract index", used)

    # index is not included
    print(entity_num)
    for key in map._numMap:
        if isdigit(key) and key not in integers:
            entity_num = entity_num - 1
    print(entity_num)
    
    # extract relation metadata
    row = 0
    relation_list = os.listdir("../../data/yago1/relations")
    total_records = 0
    types = set()
    for name in relation_list:
        relation_path = os.path.join("../../data/yago1/relations", name)
        rel_name, arity, record_cnt = parseRelFilePath(relation_path)
        num = map.name2Num(rel_name)
        total_records = total_records + record_cnt
        if rel_name == "type":
            relation = KbRelation(rel_name, num, arity, record_cnt, "../../data/yago1/relations")
            getTypes(types, relation)
    for name in relation_list:
        mem = psutil.virtual_memory()
        used = mem.free / 1024 / 1024 / 1024
        print("free mem before begin", used)
        relation_path = os.path.join("../../data/yago1/relations", name)
        rel_name, arity, record_cnt = parseRelFilePath(relation_path)
        num = map.name2Num(rel_name)
        relation = KbRelation(rel_name, num, arity, record_cnt, "../../data/yago1/relations")
        updateDegree(degrees, relation)
        row = row + 1
        # write name
        excelsheet.write(row, 0, rel_name)
        # write id
        excelsheet.write(row, 1, map.name2Num(rel_name))
        # write num of instances
        excelsheet.write(row, 2, record_cnt)
        # write propotion
        excelsheet.write(row, 3, relation.totalRecords() / total_records)
        # check if it is property
        property = checkProperty(relation, integers, types, map)
        if(property == True):
            excelsheet.write(row, 4, "true")
        else:
            excelsheet.write(row, 4, "false")        
        # extract reified info
        # TODO: reified num may be indetectable in some kb
        is_reified = checkReified(relation, integers, map)
        if(is_reified):
            excelsheet.write(row, 5, "true")
        else:
            excelsheet.write(row, 5, "false")
        # extract entity、subject、object、symmetricity
        total_entity = set()
        s_to_o = dict()
        o_to_s = dict()
        constructDict(relation, total_entity, s_to_o, o_to_s)
        excelsheet.write(row, 6, len(total_entity))
        excelsheet.write(row, 7, len(s_to_o))
        excelsheet.write(row, 8, len(o_to_s))
        print(len(total_entity), len(s_to_o), len(o_to_s))
        symmetricity_num = 0
        for key in s_to_o:
            for ob in s_to_o[key]:
                if o_to_s.get(ob) is not None:
                    for sub in o_to_s[ob]:
                        if(sub == key):
                            symmetricity_num = symmetricity_num + 1
        excelsheet.write(row, 10, symmetricity_num)
        # calculate functionality
        functionality = len(s_to_o) / len(total_entity)
        excelsheet.write(row, 9, functionality)
        del relation
        gc.collect()
        sleep(3)
        mem = psutil.virtual_memory()
        used = mem.free / 1024 / 1024 / 1024
        print("free mem after begin", used)
    # add Excel sheet1 and title info
    excelsheet = excel.add_sheet('overview')
    excelsheet.write(0, 0, "dataset")
    excelsheet.write(0, 1, "relations")
    excelsheet.write(0, 2, "entities")
    excelsheet.write(0, 3, "classes")
    excelsheet.write(0, 4, "degrees")
    excelsheet.write(1, 0, "yago1")
    excelsheet.write(1, 1, relation_num)
    excelsheet.write(1, 2, entity_num)
    excelsheet.write(1, 3, len(types))
    total_degree = 0
    for key in degrees:
        total_degree = total_degree + degrees[key]
    avg_degree = total_degree / entity_num
    excelsheet.write(1, 4, avg_degree)
    excel.save("./metadata.xls")

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
    getMeta()
