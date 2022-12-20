package converter;

import org.junit.jupiter.api.Test;
import sinc2.kb.SimpleKb;
import sinc2.util.LittleEndianIntIO;
import sinc2.util.kb.NumeratedKb;
import sinc2.util.kb.NumerationMap;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileReader;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class ConverterTest {

    static class TestIterator implements Iterator<Triple> {
        static final Triple[] TRIPLES = new Triple[] {
                new Triple("a", "r1", "b"),         // 1, 2
                new Triple("x", "rdf:type", "t1"),  // 3, 6
                new Triple("x", "r2", "y"),         // 3, 4
                new Triple("c", "r3", "c"),         // 5, 5
        };

        int idx = 0;

        @Override
        public boolean hasNext() {
            return idx < TRIPLES.length;
        }

        @Override
        public Triple next() {
            return TRIPLES[idx++];
        }
    }

    static class TestConverter extends Converter {
        public TestConverter(String outputKbName, String outputPath) {
            super(outputKbName, outputPath);
        }

        @Override
        protected Iterator<Triple> tripleIterator() {
            return new TestIterator();
        }
    }

    @Test
    void testConvert() throws Exception {
        final String OUTPUT_PATH = "/dev/shm/";
        final String OUTPUT_NAME = "TestConverter";
        TestConverter converter = new TestConverter(OUTPUT_NAME, OUTPUT_PATH);
        assertDoesNotThrow(converter::convert);

        Set<String> actual_file_names = new HashSet<>();
        Path kb_dir_path = Paths.get(OUTPUT_PATH, OUTPUT_NAME);
        File[] files = kb_dir_path.toFile().listFiles();
        assertNotNull(files);
        for (File file: files) {
            actual_file_names.add(file.getName());
        }
        assertTrue(actual_file_names.contains("0.rel"));    // r1
        assertTrue(actual_file_names.contains("1.rel"));    // rdf:type
        assertTrue(actual_file_names.contains("2.rel"));    // r2
        assertTrue(actual_file_names.contains("3.rel"));    // r3
        assertTrue(actual_file_names.contains("Relations.tsv"));    // Relation info
        assertTrue(actual_file_names.contains("map1.tsv"));    // Name strings

        /* Test relation files */
        BufferedReader reader = new BufferedReader(new FileReader(NumeratedKb.getRelInfoFilePath(OUTPUT_NAME, OUTPUT_PATH).toFile()));
        List<String> actual_rel_infos = new ArrayList<>();
        String line;
        while (null != (line = reader.readLine())) {
            actual_rel_infos.add(line);
        }
        reader.close();
        assertEquals(new ArrayList<>(List.of(
                "r1\t2\t1", "rdf:type\t2\t1", "r2\t2\t1", "r3\t2\t1"
        )), actual_rel_infos);
        SimpleKb skb = new SimpleKb(OUTPUT_NAME, OUTPUT_PATH);
        assertEquals(4, skb.totalRelations());
        assertEquals(4, skb.totalRecords());
        assertEquals("r1", skb.getRelation(0).name);
        assertEquals("rdf:type", skb.getRelation(1).name);
        assertEquals("r2", skb.getRelation(2).name);
        assertEquals("r3", skb.getRelation(3).name);
        assertEquals(1, skb.getRelation(0).totalRows());
        assertEquals(2, skb.getRelation(0).totalCols());
        assertTrue(skb.getRelation(0).hasRow(new int[]{1, 2}));
        assertEquals(1, skb.getRelation(1).totalRows());
        assertEquals(2, skb.getRelation(1).totalCols());
        assertTrue(skb.getRelation(1).hasRow(new int[]{3, 6}));
        assertEquals(1, skb.getRelation(2).totalRows());
        assertEquals(2, skb.getRelation(2).totalCols());
        assertTrue(skb.getRelation(2).hasRow(new int[]{3, 4}));
        assertEquals(1, skb.getRelation(3).totalRows());
        assertEquals(2, skb.getRelation(3).totalCols());
        assertTrue(skb.getRelation(3).hasRow(new int[]{5, 5}));

        /* Test mapping files */
        reader = new BufferedReader(new FileReader(
                NumerationMap.getMapFilePath(kb_dir_path.toString(), NumerationMap.MAP_FILE_NUMERATION_START).toFile()
        ));
        List<String> actual_mapping = new ArrayList<>();
        while (null != (line = reader.readLine())) {
            actual_mapping.add(line);
        }
        reader.close();
        assertEquals(new ArrayList<>(List.of(
                "a", "b", "x", "y", "c", "t1"
        )), actual_mapping);

        /* Test type value file */
        FileInputStream fis = new FileInputStream(Paths.get(OUTPUT_PATH, OUTPUT_NAME, Converter.TYPE_VALUES_FILE_NAME).toFile());
        List<Integer> actual_type_values = new ArrayList<>();
        byte[] buffer = new byte[Integer.BYTES];
        while (Integer.BYTES == fis.read(buffer)) {
            actual_type_values.add(LittleEndianIntIO.byteArray2LeInt(buffer));
        }
        assertEquals(new ArrayList<>(List.of(6)), actual_type_values);
    }
}