package converter.impl;

import converter.Converter;
import converter.Triple;

import java.io.*;
import java.util.Iterator;

/**
 * Iterator for YGAO-1 structure.
 */
public class Yago1Iterator implements Iterator<Triple> {

    protected File[] dirFiles;
    protected int dirIdx;
    protected File[] tripleFiles = new File[0];
    protected int tripleFileIdx;
    protected BufferedReader reader = null;
    protected String predicate;
    protected Triple nextTriple = null;
    protected long time_start;

    public Yago1Iterator(String kbPath) {
        File[] dir_files = new File(kbPath).listFiles();
        this.dirFiles = (null == dir_files) ? new File[0] : dir_files;
        for (dirIdx = 0; dirIdx < dirFiles.length; dirIdx++) {
            /* Locate the first dir */
            File dir_file = dirFiles[dirIdx];
            predicate = dir_file.getName();
            if (!dir_file.isDirectory() || Yago1Converter.NON_FACTUAL_PREDICATES.contains(predicate) ||
                    Converter.NON_FACTUAL_PREDICATES.contains(predicate)) {
                continue;
            }
            tripleFiles = dir_file.listFiles();
            tripleFiles = (null == tripleFiles) ? new File[0] : tripleFiles;
            tripleFileIdx = 0;
            time_start = System.currentTimeMillis();
            break;
        }
        dirIdx++;
    }

    @Override
    public boolean hasNext() {
        /* Exhausting current triple file */
        if (null != reader) {
            try {
                String line = reader.readLine();
                if (null == line) {
                    reader.close();
                    reader = null;
                } else {
                    String[] components = line.split("\t");
                    nextTriple = new Triple(components[1], predicate, components[2]);
                    return true;
                }
            } catch (IOException e) {
                System.err.println("Error occurred reading the file: " + tripleFiles[tripleFileIdx].getAbsolutePath());
                e.printStackTrace();
                return false;
            }
        }

        /* Change triple file */
        nextTriple = null;
        for (; tripleFileIdx < tripleFiles.length && null == nextTriple; tripleFileIdx++) {
            File triple_file = tripleFiles[tripleFileIdx];
            if (!triple_file.isFile()) {
                continue;
            }
            try {
                reader = new BufferedReader(new FileReader(triple_file));
                String line = reader.readLine();
                if (null == line) {
                    reader.close();
                    reader = null;
                } else {
                    String[] components = line.split("\t");
                    nextTriple = new Triple(components[1], predicate, components[2]);
                    /* Should not return here, "tripleFileIdx++" should take effect */
                }
            } catch (IOException e) {
                System.err.println("Failed to load triple file: " + triple_file.getAbsolutePath());
                e.printStackTrace();
                return false;
            }
        }
        if (null != nextTriple) {
            return true;
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
            tripleFiles = (null == tripleFiles) ? new File[0]: tripleFiles;
            for (tripleFileIdx = 0; tripleFileIdx < tripleFiles.length && null == nextTriple; tripleFileIdx++) {
                File triple_file = tripleFiles[tripleFileIdx];
                if (!triple_file.isFile()) {
                    continue;
                }
                try {
                    reader = new BufferedReader(new FileReader(triple_file));
                    String line = reader.readLine();
                    if (null == line) {
                        reader.close();
                        reader = null;
                    } else {
                        String[] components = line.split("\t");
                        nextTriple = new Triple(components[1], predicate, components[2]);
                    }
                } catch (IOException e) {
                    System.err.println("Failed to load triple file: " + triple_file.getAbsolutePath());
                    e.printStackTrace();
                }
            }
        }
        return null != nextTriple;
    }

    @Override
    public Triple next() {
        return nextTriple;
    }
}
