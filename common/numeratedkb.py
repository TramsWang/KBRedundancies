from glob import glob
import struct
from typing import Iterable, Set, Tuple
import os
import re
import heapq

"""
This file defines the classes and operations for the Relation, the NumerationMap, and the NumeratedKB.
"""

class KbException(Exception):
    """
    Class for Exception in the KB operations
    """
    def __init__(self, msg: str) -> None:
        self.msg = msg

def getRelFilePath(kbPath: str, relName: str, arity: int, records: int) -> str:
    """
    Return the path of a relation file

    Parameters:
        kbPath:     The input KB path.
        relName:    The name of the relation
        arity:      The arity of the relation
        records:    The number of the records in the relation
    
    Returns:
        The file path
    """
    return os.path.join(kbPath, "%s_%d_%d.rel" % (relName, arity, records))

def parseRelFilePath(path: str) -> Tuple[str, int, int]:
    """
    Parse an absolute path to three components: relation name, arity, and #records.

    Parameters:
        path:       The absolute path to a '.rel' file

    Returns:
        str:        Relation name
        int:        arity
        int:        #records
    """
    file_name = path.split(os.path.sep)[-1]
    relation_name, arity, record_cnt = re.findall("(.+)_([0-9]+)_([0-9]+).rel$", file_name)[0]
    return (relation_name, int(arity), int(record_cnt))

def getMapFilePath(kbPath: str, num: int) -> str:
    """
    Return the path of the 'num'-th map file

    Parameters:
        kbPath:     The input KB path.
        num:        The numeration of the file

    Returns:
        The file path
    """
    return os.path.join(kbPath, "map%d.tsv" % num)

def getKbPath(kbName:str, basePath: str) -> str:
    """
    Return the path of the KB files.

    Parameters:
        - kbName:   The name of the KB.
        - basePath: The base path where the KB is located.

    Returns:
        - The path where the data files of the KB is stored.
    """
    return os.path.join(basePath, kbName)

class NumerationMap:
    """
    Class for the numeration map, from name strings to numerations. Map entries can be iterated over a NumerationMap
    instance.
    """

    _MAP_FILE_NUMERATION_START = 1
    _MAX_MAP_ENTRIES = 1000000

    def __init__(self, kbPath: str = None):
        """
        Read the numeration mapping files of the KB. If no path is given, initialize an empty map.

        Parameters:
            kbPath:     The input KB path. KB is in the Numerated Format.
        """
        # Initialize an empty map
        if kbPath is None:
            
            self._numMap = dict()       # int -> str
            self._numArray = [None]     # str[]
            self._freeNums = []         # int[], numerations that are not associated with names, 
                                        # organized in minimum heap
            return
        
        # Create the map structure, from name string to numeration number
        self._numMap = dict() # int -> str
        max_num = 0
        regex = re.compile("map[0-9]+.tsv$")
        for fname in os.listdir(kbPath):
            fpath = os.path.join(kbPath, fname)
            if os.path.isfile(fpath) and regex.match(fname):
                map_file = open(fpath, 'r')
                for line in map_file.readlines():
                    name, num = line.strip().split('\t')
                    num = int(num, 16)
                    self._numMap[name] = num
                    max_num = max(max_num, num)
                map_file.close()
        
        # Create a string array, where the indices are the numeration numbers
        self._numArray = [None] * (max_num+1)
        for name, num in self._numMap.items():
            self._numArray[num] = name

        # Create a numeration set for unused numbers
        self._freeNums = []
        for num in range(1, max_num+1):
            if self._numArray[num] is None:
                heapq.heappush(self._freeNums, num)

    def mapName(self, name: str) -> int:
        """
        Add a name string into the map and assign the name a unique number. If the name has already been mapped,
        return the mapped numeration.

        Parameters:
            name:       The new name string

        Returns:
            int:        The numeration for the name
        """
        num = self._numMap.get(name, None)
        if num is not None:
            return num
        
        if 0 != len(self._freeNums):
            # Assign a free numeration that is smaller than the maximum numeration
            num = heapq.heappop(self._freeNums)
            self._numArray[num] = name
        else:
            # No free numeration is available, create a new number
            num = len(self._numArray)
            self._numArray.append(name)
        self._numMap[name] = num
        return num

    def unmapName(self, name: str) -> int:
        """
        Remove the mapping of a name string in the map.

        Parameters:
            name:       The name string that should be removed

        Returns:
            int:        The number for the name. 'None' if the name is not mapped in the map.
        """
        num = self._numMap.pop(name, None)
        if num is not None:
            self._numArray[num] = None
            heapq.heappush(self._freeNums, num)
        return num

    def unmapNumeration(self, num: int) -> str:
        """
        Remove the mapping of the number 'num' in the map.

        Parameters:
            num:        The number that should be unmapped

        Returns:
            str:        The mapped name of the number, 'None' if the number is not mapped in the map.
        """
        if 0 < num < len(self._numArray) and self._numArray[num] is not None:
            name = self._numArray[num]
            self._numArray[num] = None
            self._numMap.pop(name)
            heapq.heappush(self._freeNums, num)
            return name
        return None

    def num2Name(self, num: int) -> str:
        """
        Get the mapped name for number 'num'.

        Parameters:
            num:

        Returns:
            str:        The mapped name of the number, 'None' if the number is not mapped in the KB.
        """
        if 0 < num < len(self._numArray):
            return self._numArray[num]
        return None

    def name2Num(self, name: str) -> int:
        """
        Get the mapped number for the name

        Parameters:
            name:

        Returns:
            int:    The mapped number for the name. 'None' if the name is not mapped in the KB.
        """
        return self._numMap.get(name, None)

    def dump(self, kbPath: str, startMapNum: int = _MAP_FILE_NUMERATION_START, maxEntries: int = _MAX_MAP_ENTRIES) -> None:
        """
        Write the numeration map to 'kbPath'.

        Parameters:
            kbPath:         The input KB path.
            startMapNum:    The start number of the map files (Default _MAP_FILE_NUMERATION_START)
            maxEntries:     The maximum number of entries a map file contains (Default _MAX_MAP_ENTRIES)

        Returns:
            None
        """
        map_num = startMapNum
        map_file = open(getMapFilePath(kbPath, map_num), 'w')
        records_cnt = 0
        for name, num in self._numMap.items():
            if records_cnt >= maxEntries:
                map_file.close()
                records_cnt = 0
                map_num += 1
                map_file = open(getMapFilePath(kbPath, map_num), 'w')
            map_file.write("%s\t%x\n" % (name, num))
            records_cnt += 1
        map_file.close()

    def totalMappings(self):
        """
        Return the total number of mapping entries.

        Parameters:
            None

        Returns:
        """
        return len(self._numMap)
    
    def __iter__(self):
        return iter(self._numMap)

    @property
    def MAX_MAP_ENTRIES(self):
        return self._MAX_MAP_ENTRIES


class KbRelation:
    """
    Class for a single relation in a KB. Records can be iterated over a KbRelation instance.
    """

    __INT_SIZE = struct.calcsize('i')

    def __init__(self, name: str, numeration: int, arity: int, records: int = 0, kbPath: str = None, numMap: dict = None) -> None:
        """
        Load a single relation file from the local file system. If the 'numMap' is not 'None', every loaded numeration
        is checked for validness in the map.

        Parameters:
            name:       The name of the relation.
            numeration: The numberation number of the relation.
            arity:      The arity of the relation.
            records:    The number of records in the relation.
            kbPath:     The input KB path. Default: None
            numMap:     The mapping used for checking whether loaded numerations are mapped. Default: None

        Raises:
            KbException:    'numMap' is not None and a loaded numeration is not mapped
        """
        self._name = name
        self._numeration = numeration
        self._arity = arity
        self._records = set()

        # Initialize empty relation
        if kbPath is None:
            return
        
        # Read relation from file
        with open(getRelFilePath(kbPath, name, arity, records), 'rb') as ifd:
            buffer_size = KbRelation.__INT_SIZE * arity
            format_str = self.__getRecordFormatString(arity)
            i = 0
            if numMap is not None:
                while i < records:
                    record = struct.unpack(format_str, ifd.read(buffer_size))
                    for num in record:
                        if numMap.num2Name(num) is None:
                            raise KbException("Loaded numeration is not mapped: %d" % num)
                    self._records.add(record)
                    i += 1
            else:
                while i < records:
                    record = struct.unpack(format_str, ifd.read(buffer_size))
                    self._records.add(record)
                    i += 1

    def addRecord(self, record: tuple) -> None:
        """
        Add a record to the relation

        Parameters:
            record:     The record that should be added to the relation. A record is a tuple fo integers.

        Returns:
            None

        Raises:
            KbException:    The arity of the record does not match that of the relation.
        """
        if len(record) != self._arity:
            raise KbException("Record arity (%d) does not match the relation (%d): %s" % (len(record), self._arity, record))
        self._records.add(record)

    def addRecords(self, records: Iterable[tuple]) -> None:
        """
        Add a batch of records to the relation

        Parameters:
            records:    An iterable object of records.
        
        Returns:
            None

        Raises:
            KbException:    The arity of the record does not match that of the relation.
        """
        for record in records:
            if len(record) != self._arity:
                raise KbException("Record arity (%d) does not match the relation (%d): %s" % (len(record), self._arity, record))
        self._records.update(records)

    def removeRecord(self, record: tuple) -> None:
        """
        Remove a record from the relation

        Parameters:
            record:     The record that should be removed

        Returns:
            None
        """
        self._records.discard(record)

    def dump(self, kbPath: str) -> None:
        """
        Write a KbRelation object to a '.rel' file.

        Parameters:
            kbPath:     The input KB path.
            kbRel:      A KbRelation object.

        Returns:
            None

        Files are written in the file system and nothing is returned.
        """
        ofd = open(getRelFilePath(kbPath, self._name, self._arity, len(self._records)), 'wb')
        format_str = self.__getRecordFormatString(self._arity)
        for record in self._records:
            ofd.write(struct.pack(format_str, *record))
        ofd.close()

    def hasRecord(self, record: tuple) -> bool:
        return record in self._records

    def __iter__(self):
        return iter(self._records)

    def __getRecordFormatString(self, arity: int) -> str:
        return '<' + 'i' * arity

    def getName(self) -> str:
        return self._name

    def getArity(self) -> int:
        return self._arity
        
    def getRecordSet(self) -> set:
        return self._records

    def totalRecords(self) -> int:
        return len(self._records)

    def getNumeration(self) -> int:
        return self._numeration

class NumeratedKb:
    """
    Class for a single knowledge base.
    """

    def __init__(self, name: str, basePath: str = None, check: bool = False) -> None:
        """
        Load a KB from the path 'kbPath'

        Parameters:
            name:       The name of the KB.
            basePath:   The path where the KB is stored. Default: None
            check:      Whether loaded records are checked in the mapping

        Raises:
            KbException:    Numerations in loaded records are not mapped.
        """
        self._name = name
        self._relations = dict()        # relation numeration: int -> relation object: KbRelation

        # Create Empty Kb
        if basePath is None:
            self._numMap = NumerationMap()
            return

        # Construct Path
        kbPath = getKbPath(name, basePath)
        
        # Load Maps
        self._numMap = NumerationMap(kbPath)

        # Load Relations
        for rel_file_path in glob("%s/*.rel" % kbPath):
            rel_name, arity, record_cnt = parseRelFilePath(rel_file_path)
            num = self._numMap.name2Num(rel_name)
            if check:
                relation = KbRelation(rel_name, num, arity, record_cnt, kbPath, self._numMap)
            else:
                relation = KbRelation(rel_name, num, arity, record_cnt, kbPath)
            self._relations[num] = relation

    def dump(self, basePath: str) -> None:
        """
        Dump a KB to the file system. If the path does not exist, it will be created.

        Parameters:
            basePath:   The path where the KB will be stored.

        Returns:
            None

        Raises:
            Exception:  Directory creation error
        """
        # Check & Create dir
        kbPath = os.path.join(basePath, self._name)
        if os.path.exists(kbPath):
            if not os.path.isdir(kbPath):
                raise Exception("Dump path is not a directory: %s" % kbPath)
        else:
            os.makedirs(kbPath, 0o755)

        # Dump
        self._numMap.dump(kbPath)
        for relation in self._relations.values():
            if 0 < relation.totalRecords():  # Dump only non-empty relations
                relation.dump(kbPath)

    def createRelation(self, relName: str, arity: int) -> KbRelation:
        """
        Create an empty relation in the KB. If the name 'relName' has been used, raise a KbException.

        Parameters:
            relName:    The name of the relation.
            arity:      The arity of the relation.

        Returns:
            KbRelation: The created relation

        Raises:
            KbException:    The name 'relName' has already been used.
        """
        num = self._numMap.name2Num(relName)
        if num is not None:
            if num in self._relations:
                raise KbException("The relation name has already been used: %s" % relName)
        else:
            num = self._numMap.mapName(relName)
        relation = KbRelation(relName, num, arity, 0)
        self._relations[num] = relation
        return relation

    def loadRelation(self, relBasePath: str, relName: str, arity: int, records: int, check: bool = False) -> KbRelation:
        """
        Load a relation into the KB from a '.rel' file.  If the name 'relName' has been used, raise a KbException.

        Parameters:
            relBasePath:    The path where the file is stored.
            relName:        The name of the relation.
            arity:          The arity of the relation.
            records:        The number of records in the relation.
            check:          Whether loaded records are checked in the mapping

        Returns:
            KbRelation:     The loaded relation

        Raises:
            KbException:    The name 'relName' has already been used; numerations in loaded records are not mapped.
        """
        num = self._numMap.name2Num(relName)
        if num is not None:
            if num in self._relations:
                raise KbException("The relation name has already been used: %s" % relName)
        else:
            num = self._numMap.mapName(relName)
        
        if check:
            # Check record numerations
            relation = KbRelation(relName, num, arity, records, relBasePath, self._numMap)
        else:
            relation = KbRelation(relName, num, arity, records, relBasePath)
        self._relations[num] = relation
        return relation

    def deleteRelation(self, relNum: int) -> KbRelation:
        """
        Remove a relation from the KB.

        Parameters:
            relNum:    The numeration of the relation that should be removed

        Returns:
            KbRelation: The removed relation. 'None' if there is no such relation in the KB.
        """
        return self._relations.pop(relNum, None)

    def getRelationByName(self, relName: str) -> KbRelation:
        """
        Fetch the relation in the KB by name.

        Parameters:
            relName:    The name of the relation
        
        Returns:
            KbRelation: The relation with name 'relName'. 'None' if there is no such relation in the KB.
        """
        return self._relations.get(self._numMap.name2Num(relName), None)

    def getRelationByNumeration(self, relNum: int) -> KbRelation:
        """
        Fetch the relation in the KB by numeration.

        Parameters:
            relNum:    The numeration of the relation
        
        Returns:
            KbRelation: The relation with name 'relNum'. 'None' if there is no such relation in the KB.
        """
        return self._relations.get(relNum, None)

    def hasRelationByName(self, relName: str) -> bool:
        """
        Check if there is a relation named 'relName' in the KB

        Parameters:
            relName:    The name of the relation
        
        Returns:
            bool:
        """
        return self._numMap.name2Num(relName) in self._relations

    def hasRelationByNumeration(self, relNum: int) -> bool:
        """
        Check if there is a relation numbered 'relNum' in the KB

        Parameters:
            relNum:    The numeration of the relation
        
        Returns:
            bool:
        """
        return relNum in self._relations

    def getRelationArityByName(self, relName: str) -> int:
        """
        Get the arity of relation 'relName' in the KB.

        Parameters:
            relName:    The name of the relation
        
        Returns:
            int:        'None' if the relation is not in the KB.
        """
        relation = self.getRelationByName(relName)
        if relation is not None:
            return relation.getArity()
        return None

    def getRelationArityByNumeration(self, relNum: int) -> int:
        """
        Get the arity of relation numbered 'relNum' in the KB.

        Parameters:
            relName:    The name of the relation
        
        Returns:
            int:        'None' if the relation is not in the KB.
        """
        relation = self.getRelationByNum(relNum)
        if relation is not None:
            return relation.getArity()
        return None

    def addNamedRecord2RelationByName(self, relName: str, record: tuple) -> None:
        """
        Add a record where arguments are name strings to the KB. The names will be converted to numerations (or 
        be added to the mapping first) before the record is added. A new KbRelation wil be created If the relation
        does not exist in the KB.

        Parameters:
            - relName:  The relation name
            - record:   The record where arguments are name strings

        Returns:
            - None

        Raises:
            - KbException:  Record arity does not match the relation.
        """
        relation = self.getRelationByName(relName)
        if relation is None:
            relation = self.createRelation(relName, len(record))
        
        arity = relation.getArity()
        if len(record) != arity:
            raise KbException("Record arity (%d) does not match the relation (%d): %s" % (len(record), arity, record))

        num_record = [self._numMap.mapName(record[i]) for i in range(arity)]
        relation.addRecord(tuple(num_record))

    def addNamedRecord2RelationByNumeration(self, relNum: int, record: tuple) -> None:
        """
        Add a record where arguments are name strings to the KB. The names will be converted to numerations (or 
        be added to the mapping first) before the record is added. A KbException will be raised If the relation
        does not exist in the KB.

        Parameters:
            - relNum:   The relation numeration
            - record:   The record where arguments are name strings

        Returns:
            - None

        Raises:
            - KbException:  The relation is not in the KB; Record arity does not match the relation.
        """
        relation = self.getRelationByNumeration(relNum)
        if relation is None:
            raise KbException("Relation is not in the KB: %d" % relNum)
        
        arity = relation.getArity()
        if len(record) != arity:
            raise KbException("Record arity (%d) does not match the relation (%d): %s" % (len(record), arity, record))

        num_record = [self._numMap.mapName(record[i]) for i in range(arity)]
        relation.addRecord(tuple(num_record))

    def addNumeratedRecord2RelationByName(self, relName: str, record: tuple) -> None:
        """
        Add a record where arguments are numbers to the KB. A new KbRelation will be created If the relation does
         not exist in the KB. A KbException will be raised if a number is not mapped to any string in the KB.

        Parameters:
            - relName:  The relation name
            - record:   The record where arguments are numbers

        Returns:
            - None

        Raises:
            - KbException:  Record arity does not match the relation; Number is not mapped to any string
        """
        relation = self.getRelationByName(relName)
        if relation is None:
            relation = self.createRelation(relName, len(record))
        
        arity = relation.getArity()
        if len(record) != arity:
            raise KbException("Record arity (%d) does not match the relation (%d): %s" % (len(record), arity, record))

        for i in record:
            if self._numMap.num2Name(i) is None:
                raise KbException("Numeration not mapped in the KB: %d" % i)
        
        relation.addRecord(record)

    def addNumeratedRecord2RelationByNumeration(self, relNum: int, record: tuple) -> None:
        """
        Add a record where arguments are numbers to the KB. A KbException will be raised if a number is not mapped
        to any string in the KB or the relation does not exist.

        Parameters:
            - relNum:   The relation numeration
            - record:   The record where arguments are numbers

        Returns:
            - None

        Raises:
            - KbException:  Relation does not exist; Record arity does not match the relation; Number is not
            mapped to any string
        """
        relation = self.getRelationByNumeration(relNum)
        if relation is None:
            raise KbException("Relation is not in the KB: %d" % relNum)
        
        arity = relation.getArity()
        if len(record) != arity:
            raise KbException("Record arity (%d) does not match the relation (%d): %s" % (len(record), arity, record))

        for i in range(arity):
            if self._numMap.num2Name(record[i]) is None:
                raise KbException("Numeration not mapped in the KB: %d" % record[i])
        
        relation.addRecord(record)

    def addNamedRecords2RelationByName(self, relName: int, records: Iterable[tuple]) -> None:
        """
        Add records where arguments are name strings to the KB. The names will be converted to numerations (or 
        be added to the mapping first) before the record is added. A new KbRelation wil be created If the relation
        does not exist in the KB.

        Parameters:
            - relName:  The relation name
            - record:   The record where arguments are name strings

        Returns:
            - None

        Raises:
            - KbException:  Record arity does not match the relation.
        """
        if 0 == len(records):
            return

        relation = self.getRelationByName(relName)
        if relation is None:
            try:
                relation = self.createRelation(relName, len(next(iter(records))))
            except StopIteration:
                # If no record is in 'records', simply return
                return
        
        arity = relation.getArity()
        for record in records:
            if len(record) != arity:
                raise KbException("Record arity (%d) does not match the relation (%d): %s" % (len(record), arity, record))

            num_record = [0] * arity
            for i in range(arity):
                num = self._numMap.name2Num(record[i])
                if num is None:
                    num = self._numMap.mapName(record[i])
                num_record[i] = num
            
            relation.addRecord(tuple(num_record))

    def addNamedRecords2RelationByNumeration(self, relNum: int, records: Iterable[tuple]) -> None:
        """
        Add a record where arguments are name strings to the KB. The names will be converted to numerations (or 
        be added to the mapping first) before the record is added. A KbException wil be raised If the relation
        does not exist in the KB.

        Parameters:
            - relNum:   The relation numeration
            - record:   The record where arguments are name strings

        Returns:
            - None

        Raises:
            - KbException:  The relation is not in the KB; Record arity does not match the relation.
        """
        relation = self.getRelationByNumeration(relNum)
        if relation is None:
            raise KbException("Relation is not in the KB: %d" % relNum)
        
        arity = relation.getArity()
        for record in records:
            if len(record) != arity:
                raise KbException("Record arity (%d) does not match the relation (%d): %s" % (len(record), arity, record))

            num_record = [0] * arity
            for i in range(arity):
                num = self._numMap.name2Num(record[i])
                if num is None:
                    num = self._numMap.mapName(record[i])
                num_record[i] = num
            
            relation.addRecord(tuple(num_record))

    def addNumeratedRecords2RelationByName(self, relName: str, records: Iterable[tuple]) -> None:
        """
        Add a record where arguments are numbers to the KB. A new KbRelation wil be created If the relation does
         not exist in the KB. A KbException will be raised if a number is not mapped to any string in the KB.

        Parameters:
            - relName:  The relation name
            - record:   The record where arguments are numbers

        Returns:
            - None

        Raises:
            - KbException:  Record arity does not match the relation; Number is not mapped to any string
        """
        relation = self.getRelationByName(relName)
        if relation is None:
            try:
                relation = self.createRelation(relName, len(next(iter(records))))
            except StopIteration:
                # If no record is in 'records', simply return
                return
        
        arity = relation.getArity()
        for record in records:
            if len(record) != arity:
                raise KbException("Record arity (%d) does not match the relation (%d): %s" % (len(record), arity, record))

            for i in range(arity):
                if self._numMap.num2Name(record[i]) is None:
                    raise KbException("Numeration not mapped in the KB: %d" % record[i])
            
            relation.addRecord(record)

    def addNumeratedRecords2RelationByNumeration(self, relNum: int, records: Iterable[tuple]) -> None:
        """
        Add a record where arguments are numbers to the KB. A KbException will be raised if a number is not mapped
        to any string in the KB or the relation does not exist.

        Parameters:
            - relNum:   The relation numeration
            - record:   The record where arguments are numbers

        Returns:
            - None

        Raises:
            - KbException:  Relation does not exist; Record arity does not match the relation; Number is not
            mapped to any string
        """
        relation = self.getRelationByNumeration(relNum)
        if relation is None:
            raise KbException("Relation is not in the KB: %d" % relNum)
        
        arity = relation.getArity()
        for record in records:
            if len(record) != arity:
                raise KbException("Record arity (%d) does not match the relation (%d): %s" % (len(record), arity, record))

            for i in range(arity):
                if self._numMap.num2Name(record[i]) is None:
                    raise KbException("Numeration not mapped in the KB: %d" % record[i])
            
            relation.addRecord(record)

    def removeNamedRecordFromRelationByName(self, relName: str, record: tuple) -> None:
        """
        Remove a record from relation 'relName'. No exception is raised if the relation is not in the KB nor the
        record is not in the relation.

        Parameters:
            relName:    The name of the relation
            record:     The record to be removed, arguments are name strings
        
        Returns:
            None
        """
        relation = self.getRelationByName(relName)
        if relation is not None:
            num_record = tuple(self._numMap.name2Num(name) for name in record)
            relation.removeRecord(num_record)

    def removeNamedRecordFromRelationByNumeration(self, relNum: int, record: tuple) -> None:
        """
        Remove a record from relation 'relName'. No exception is raised if the relation is not in the KB or the
        record is not in the relation.

        Parameters:
            relName:    The name of the relation
            record:     The record to be removed, arguments are name strings
        
        Returns:
            None
        """
        relation = self.getRelationByNumeration(relNum)
        if relation is not None:
            num_record = tuple(self._numMap.name2Num(name) for name in record)
            relation.removeRecord(num_record)

    def removeNumeratedRecordFromRelationByName(self, relName: str, record: tuple) -> None:
        """
        Remove a record from relation 'relName'. No exception is raised if the relation is not in the KB or the
        record is not in the relation.

        Parameters:
            relName:    The name of the relation
            record:     The record to be removed, arguments are numbers
        
        Returns:
            None
        """
        relation = self.getRelationByName(relName)
        if relation is not None:
            relation.removeRecord(record)

    def removeNumeratedRecordFromRelationByNumeration(self, relNum: int, record: tuple) -> None:
        """
        Remove a record from relation 'relName'. No exception is raised if the relation is not in the KB or the
        record is not in the relation.

        Parameters:
            relName:    The name of the relation
            record:     The record to be removed, arguments are numbers
        
        Returns:
            None
        """
        relation = self.getRelationByNumeration(relNum)
        if relation is not None:
            relation.removeRecord(record)

    def hasNamedRecordInRelationByName(self, relName: str, record: tuple) -> bool:
        """
        Check if a record is in the KB.

        Parameters:
            relName:    The relation name
            record:     The record, arguments are name strings

        Returns:
            bool:       True if and only if the KB has the relation and the relation contains the record
        """
        relation = self.getRelationByName(relName)
        if relation is not None:
            num_record = tuple(self._numMap.name2Num(name) for name in record)
            return relation.hasRecord(num_record)
        return False

    def hasNamedRecordInRelationByNumeration(self, relNum: int, record: tuple) -> bool:
        """
        Check if a record is in the KB.

        Parameters:
            relName:    The relation name
            record:     The record, arguments are name strings

        Returns:
            bool:       True if and only if the KB has relation and the relation contains the record
        """
        relation = self.getRelationByNumeration(relNum)
        if relation is not None:
            num_record = tuple(self._numMap.name2Num(name) for name in record)
            return relation.hasRecord(num_record)
        return False

    def hasNumeratedRecordInRelationByName(self, relName: str, record: tuple) -> bool:
        """
        Check if a record is in the KB.

        Parameters:
            relName:    The relation name
            record:     The record, arguments are numbers

        Returns:
            bool:       True if and only if the KB has relation and the relation contains the record
        """
        relation = self.getRelationByName(relName)
        if relation is not None:
            return relation.hasRecord(record)
        return False

    def hasNumeratedRecordInRelationByNumeration(self, relNum: int, record: tuple) -> bool:
        """
        Check if a record is in the KB.

        Parameters:
            relName:    The relation name
            record:     The record, arguments are numbers

        Returns:
            bool:       True if and only if the KB has relation and the relation contains the record
        """
        relation = self.getRelationByNumeration(relNum)
        if relation is not None:
            return relation.hasRecord(record)
        return False

    def mapName(self, name: str) -> int:
        """
        Add a name string into the KB and assign the name a unique number.

        Parameters:
            name:       The new name string

        Returns:
            int:        The number for the name
        """
        return self._numMap.mapName(name)

    def unmapName(self, name: str) -> int:
        """
        Remove the mapping of a name string in the KB.

        Parameters:
            name:       The name string that should be removed

        Returns:
            int:        The number for the name. 'None' if the name is not mapped in the KB.
        """
        return self._numMap.unmapName(name)

    def unmapNumeration(self, num: int) -> str:
        """
        Remove the mapping of the number 'num' in the KB.

        Parameters:
            num:        The number that should be unmapped

        Returns:
            str:        The mapped name of the number, 'None' if the number is not mapped in the KB.
        """
        return self._numMap.unmapNumeration(num)

    def num2Name(self, num: int) -> str:
        """
        Get the mapped name for number 'num'.

        Parameters:
            num:

        Returns:
            str:        The mapped name of the number, 'None' if the number is not mapped in the KB.
        """
        return self._numMap.num2Name(num)

    def name2Num(self, name: str) -> int:
        """
        Get the mapped number for the name

        Parameters:
            name:

        Returns:
            int:    The mapped number for the name. 'None' if the name is not mapped in the KB.
        """
        return self._numMap.name2Num(name)

    def getName(self) -> str:
        return self._name

    def getRelationSet(self) -> set:
        return self._relations.values()

    def getNumerationMap(self) -> NumerationMap:
        return self._numMap

    def totalMappings(self) -> int:
        return self._numMap.totalMappings()

    def totalRelations(self) -> int:
        return len(self._relations)

    def totalRecords(self) -> int:
        cnt = 0
        for relation in self._relations.values():
            cnt += relation.totalRecords()
        return cnt

    # Todo: Tidy up the mapping and records because there may be many mappings that are not used due to removal
    #       of relations and records.
    def tidyUp(self) -> None:
        raise KbException("Not Implemented")