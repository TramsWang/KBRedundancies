package converter;

import sinc2.kb.SimpleKb;
import sinc2.kb.SimpleRelation;
import sinc2.util.kb.NumeratedKb;
import sinc2.util.kb.NumerationMap;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class OldFormat2New {
    /**
     * The class for the parsed information of a relation file name
     */
    public static class RelationInfo {
        public final String name;
        public final int arity;
        public final int totalRecords;

        public RelationInfo(String name, int arity, int totalRecords) {
            this.name = name;
            this.arity = arity;
            this.totalRecords = totalRecords;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            RelationInfo that = (RelationInfo) o;
            return arity == that.arity && totalRecords == that.totalRecords && Objects.equals(name, that.name);
        }

        @Override
        public int hashCode() {
            return Objects.hash(name, arity, totalRecords);
        }
    }

    /** A regex pattern used to parse the relation file name */
    protected static final Pattern REL_FILE_NAME_PATTERN = Pattern.compile("(.+)_([0-9]+)_([0-9]+).rel$");
    /** A regex pattern used to parse the mapping file name */
    protected static final Pattern MAP_FILE_NAME_PATTERN = Pattern.compile("map[0-9]+.tsv");

    /**
     * Parse the file name of a relation to the components: relation name, arity, total records.
     */
    public static RelationInfo parseRelFilePath(String relFileName) {
        Matcher matcher = REL_FILE_NAME_PATTERN.matcher(relFileName);
        if (matcher.find()) {
            return new RelationInfo(
                    matcher.group(1), Integer.parseInt(matcher.group(2)), Integer.parseInt(matcher.group(3))
            );
        }
        return null;
    }

    public static void main(String[] args) throws ConverterException, IOException {
        if (3 != args.length) {
            System.err.println("Usage: <Path to old KB> <Old KB name> <Path to new KB>");
            return;
        }

        final String old_path = args[0];
        final String old_kb_name = args[1];
        final String new_path = args[2];
        convert(old_path, old_kb_name, new_path);
    }

    static void convert(String oldPath, String oldKBName, String newPath) throws IOException, ConverterException {
        /* Load original relations and mappings */
        File old_dir_path = NumeratedKb.getKbPath(oldKBName, oldPath).toFile();
        File[] kb_files = old_dir_path.listFiles();
        if (null == kb_files) {
            System.err.println("Cannot list files in dir: " + old_dir_path.getAbsolutePath());
            return;
        }
        System.out.print("Loading original data ...");
        long time_start = System.currentTimeMillis();
        List<int[][]> relations = new ArrayList<>();
        List<String> relation_names = new ArrayList<>();
        Map<String, Integer> map = new HashMap<>();
        for (File kb_file: kb_files) {
            RelationInfo rel_info = parseRelFilePath(kb_file.getName());
            if (null != rel_info) {
                relations.add(SimpleRelation.loadFile(kb_file, rel_info.arity, rel_info.totalRecords));
                relation_names.add(rel_info.name);
            } else if (MAP_FILE_NAME_PATTERN.matcher(kb_file.getName()).matches()) {
                BufferedReader reader = new BufferedReader(new FileReader(kb_file));
                String line;
                while (null != (line = reader.readLine())) {
                    String[] components = line.split("\t");
                    map.put(components[0], Integer.parseInt(components[1], 16));
                }
                reader.close();
            }
        }
        SimpleKb kb = new SimpleKb(oldKBName, relations.toArray(new int[0][][]), relation_names.toArray(new String[0]));
        NumerationMap num_map = new NumerationMap(map);
        long time_loaded = System.currentTimeMillis();
        System.out.printf("Done (%d ms)\n", time_loaded - time_start);

        /* Re-arrange the order of numerations to make them more concentrate in each relation */
        System.out.print("Rearranging mappings ... ");
        int[] old_2_new = new int[num_map.totalMappings()+1];    // Old integer numerations to new, i.e., old_2_new[old_num] = new_num
        int next_num = 1;
        for (SimpleRelation relation: kb.getRelations()) {
            for (int[] record: relation) {
                for (int arg_idx = 0; arg_idx < record.length; arg_idx++) {
                    int old_arg = record[arg_idx];
                    if (0 == old_2_new[old_arg]) {
                        old_2_new[old_arg] = next_num;
                        record[arg_idx] = next_num;
                        next_num++;
                    } else {
                        record[arg_idx] = old_2_new[old_arg];
                    }
                }
            }
        }
        if (next_num < old_2_new.length) {
            System.err.printf(
                    "Numeration rearrange warning: %d numerations expected, but %d rearranged (%d missing)\n",
                    old_2_new.length - 1, next_num - 1, old_2_new.length - next_num
            );
        }
        long time_rearranged = System.currentTimeMillis();
        System.out.printf("Done (%d ms)\n", time_rearranged - time_loaded);

        /* Dump KB and relations */
        System.out.print("Dumping ...");
        String[] mapped_names = new String[next_num];
        for (int old_num = 1; old_num < old_2_new.length; old_num++) {
            mapped_names[old_2_new[old_num]] = num_map.num2Name(old_num);
        }
        kb.dump(newPath, mapped_names);
        long time_dumped = System.currentTimeMillis();
        System.out.printf("Done (%d ms)\n", time_dumped - time_rearranged);
        System.out.printf("Total Time: %d ms\n", time_dumped - time_start);
    }
}
