package converter.impl;

import converter.Converter;
import converter.ConverterException;
import converter.Triple;

import java.io.*;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Set;

/**
 * Iterator for YGAO-1 structure.
 */
public class Yago1Iterator implements Iterator<Triple> {

    /** The directory of facts */
    protected static final String FACTS_DIR = "facts";
    /** The directory of entities */
    protected static final String ENTITIES_DIR = "entities";

    protected Set<String> entities = new HashSet<>();
    protected File[] dirFiles;
    protected int dirIdx;
    protected File[] tripleFiles = new File[0];
    protected int tripleFileIdx;
    protected BufferedReader reader = null;
    protected String predicate;
    protected Triple nextTriple = null;
    protected long time_start;

    public Yago1Iterator(String kbPath) throws ConverterException {
        /* Load entities */
        File entity_dir_file = Paths.get(kbPath, ENTITIES_DIR).toFile();
        File[] entities_files = entity_dir_file.listFiles();
        if (null == entities_files) {
            throw new ConverterException("Cannot list entity files in dir: " + entity_dir_file.getAbsolutePath());
        }
        for (File entity_file: entities_files) {
            try (BufferedReader reader = new BufferedReader(new FileReader(entity_file))) {
                String line;
                while (null != (line = reader.readLine())) {
                    entities.add(line.split("\t")[0]);
                }
            } catch (IOException e) {
                throw new ConverterException(e);
            }
        }

        /* Load facts */
        File fact_dir_file = Paths.get(kbPath, FACTS_DIR).toFile();
        this.dirFiles = fact_dir_file.listFiles();
        if (null == this.dirFiles) {
            throw new ConverterException("Cannot list fact files in dir: " + fact_dir_file.getAbsolutePath());
        }
        for (dirIdx = 0; dirIdx < dirFiles.length; dirIdx++) {
            /* Locate the first dir */
            File dir_file = dirFiles[dirIdx];
            predicate = dir_file.getName();
            if (!dir_file.isDirectory() || Yago1Converter.NON_FACTUAL_PREDICATES.contains(predicate) ||
                    Converter.NON_FACTUAL_PREDICATES.contains(predicate)) {
                continue;
            }
            tripleFiles = dir_file.listFiles();
            if (null == tripleFiles) {
                System.err.println("Warning: Cannot list facts in path: " + dir_file.getAbsolutePath());
                tripleFiles = new File[0];
            }
            tripleFileIdx = 0;
            time_start = System.currentTimeMillis();
            break;
        }
        dirIdx++;
    }

    @Override
    public boolean hasNext() {
        /* Exhausting current triple file */
        nextTriple = null;
        if (null != reader) {
            try {
                while (null == nextTriple) {
                    String line = reader.readLine();
                    if (null == line) {
                        reader.close();
                        reader = null;
                        break;
                    } else {
                        String[] components = line.split("\t");
                        if (entities.contains(components[1]) && entities.contains(components[2])) {
                            /* Only convert triples between two entities */
                            nextTriple = new Triple(components[1], predicate, components[2]);
                            return true;
                        }
                    }
                }
            } catch (IOException e) {
                System.err.println("Error occurred reading the file: " + tripleFiles[tripleFileIdx].getAbsolutePath());
                e.printStackTrace();
                return false;
            }
        }

        /* Change triple file */
        for (; tripleFileIdx < tripleFiles.length && null == nextTriple; tripleFileIdx++) {
            File triple_file = tripleFiles[tripleFileIdx];
            if (!triple_file.isFile()) {
                continue;
            }
            try {
                reader = new BufferedReader(new FileReader(triple_file));
                while (null == nextTriple) {
                    String line = reader.readLine();
                    if (null == line) {
                        reader.close();
                        reader = null;
                        break;
                    } else {
                        String[] components = line.split("\t");
                        if (entities.contains(components[1]) && entities.contains(components[2])) {
                            /* Only convert triples between two entities */
                            nextTriple = new Triple(components[1], predicate, components[2]);
                            tripleFileIdx++;
                            return true;
                        }
                    }
                }
            } catch (IOException e) {
                System.err.println("Failed to load triple file: " + triple_file.getAbsolutePath());
                e.printStackTrace();
                return false;
            }
        }

        /* Change dir file */
        long time_done = System.currentTimeMillis();
        System.out.printf(
                "Relation '%s' loaded (%d ms, %d/%d finished)\n", dirFiles[dirIdx-1].getName(),
                time_done - time_start, dirIdx, dirFiles.length
        );
        time_start = time_done;
        for (; dirIdx < dirFiles.length && null == nextTriple; dirIdx++) {
            File dir_file = dirFiles[dirIdx];
            predicate = dir_file.getName();
            if (!dir_file.isDirectory() || Yago1Converter.NON_FACTUAL_PREDICATES.contains(predicate) ||
                    Converter.NON_FACTUAL_PREDICATES.contains(predicate)) {
                continue;
            }
            tripleFiles = dir_file.listFiles();
            if (null == tripleFiles) {
                System.err.println("Warning: Cannot list facts in path: " + dir_file.getAbsolutePath());
                tripleFiles = new File[0];
            }
            for (tripleFileIdx = 0; tripleFileIdx < tripleFiles.length && null == nextTriple; tripleFileIdx++) {
                File triple_file = tripleFiles[tripleFileIdx];
                if (!triple_file.isFile()) {
                    continue;
                }
                try {
                    reader = new BufferedReader(new FileReader(triple_file));
                    while (null == nextTriple) {
                        String line = reader.readLine();
                        if (null == line) {
                            reader.close();
                            reader = null;
                            break;
                        } else {
                            String[] components = line.split("\t");
                            if (entities.contains(components[1]) && entities.contains(components[2])) {
                                /* Only convert triples between two entities */
                                nextTriple = new Triple(components[1], predicate, components[2]);
                                tripleFileIdx++;
                                dirIdx++;
                                return true;
                            }
                        }
                    }
                } catch (IOException e) {
                    System.err.println("Failed to load triple file: " + triple_file.getAbsolutePath());
                    e.printStackTrace();
                }
            }
        }
        return false;
    }

    @Override
    public Triple next() {
        return nextTriple;
    }
}
