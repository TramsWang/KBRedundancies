package sampler;

import sinc2.common.Record;
import sinc2.kb.SimpleKb;
import sinc2.kb.SimpleRelation;
import sinc2.sampling.Edge;
import sinc2.sampling.Sampler;
import sinc2.sampling.SamplingInfo;
import sinc2.util.LittleEndianIntIO;
import sinc2.util.io.IntWriter;
import sinc2.util.kb.NumeratedKb;
import sinc2.util.kb.NumerationMap;

import java.io.*;
import java.nio.file.Paths;
import java.util.*;

/**
 * Sampling edges of major nodes in KGs. Type nodes are not selected as major nodes.
 */
public class MajorNodeSampler extends Sampler {

    public static final String CONST_MAP_FILE_NAME = "ConstMap.dat";

    static class SimpleNode {
        public final int num;
        public final List<Edge> edges = new ArrayList<>();

        public SimpleNode(int num) {
            this.num = num;
        }
    }

    protected final Set<Integer> typeValues;

    public MajorNodeSampler(Set<Integer> typeValues) {
        this.typeValues = typeValues;
    }

    @Override
    public SamplingInfo sample(SimpleKb originalKb, int budget, String sampledKbName) {
        /* Build the adjacent list of each constant */
        System.out.println("Building adjacent list ...");
        long time_start = System.currentTimeMillis();
        SimpleNode[] nodes = new SimpleNode[originalKb.totalConstants()+1];
        for (int i = 0; i < nodes.length; i++) {
            nodes[i] = new SimpleNode(i);
        }
        SimpleRelation[] relations = originalKb.getRelations();
        String[] rel_names = new String[relations.length];
        List<Set<Record>> sampled_relations = new ArrayList<>(relations.length);
        for (int i = 0; i < relations.length; i++) {
            SimpleRelation relation = relations[i];
            rel_names[i] = relation.name;
            sampled_relations.add(new HashSet<>());
            for (int[] row: relation) {
                Edge edge = new Edge(row[0], relation.id, row[1]);
                nodes[row[0]].edges.add(edge);
                nodes[row[1]].edges.add(edge);
            }
        }
        long time_adjacent_complete = System.currentTimeMillis();
        System.out.printf("Done (%d s)\n", (time_adjacent_complete - time_start) / 1000);

        /* Select major nodes, that is, ones with the largest degrees and the node is not a type entity */
        System.out.println("Selecting major nodes ...");
        Arrays.sort(nodes, Comparator.comparingInt((SimpleNode n) -> n.edges.size()).reversed());
        int sampled_edges = 0;
        for (int i = 0; i < nodes.length && sampled_edges < budget; i++) {
            SimpleNode node = nodes[i];
            if (typeValues.contains(node.num)) {
                continue;
            }
            sampled_edges += node.edges.size();
            for (Edge edge: node.edges) {
                sampled_relations.get(edge.pred).add(new Record(new int[]{edge.subj, edge.obj}));
            }
        }
        long time_selected = System.currentTimeMillis();
        System.out.printf("Done (%d s)\n", (time_selected - time_adjacent_complete) / 1000);

        /* Format the sampled KB */
        System.out.println("Reformatting sampled KB ...");
        SamplingInfo ret = formatSampledKb(sampledKbName, sampled_relations, rel_names);
        long time_formatted = System.currentTimeMillis();
        System.out.printf("Done (%d s)\n", (time_formatted - time_selected) / 1000);
        System.out.printf("Total Sampling Time: %d s\n", (time_formatted - time_start) / 1000);
        return ret;
    }

    public static void main(String[] args) throws IOException {
        if (5 != args.length) {
            System.out.println("Usage: <Input Path> <Original KB Name> <Output Path> <Sampled KB Name> <Budget>");
            return;
        }
        final String input_path = args[0];
        final String original_kb_name = args[1];
        final String output_path = args[2];
        final String sampled_kb_name = args[3];
        final int budget = Integer.parseInt(args[4]);

        System.out.println("Loading original KB ...");
        long time_start = System.currentTimeMillis();
        SimpleKb original_kb = new SimpleKb(original_kb_name, input_path);
        long time_loaded = System.currentTimeMillis();
        System.out.printf("Done (%d s)\n", (time_loaded - time_start) / 1000);
        SamplingInfo sampled_info = new MajorNodeSampler(loadTypeValues(original_kb_name, input_path))
                .sample(original_kb, budget, sampled_kb_name);
        long time_sampled = System.currentTimeMillis();
        System.out.println("Dumping ...");
        sampled_info.sampledKb.dump(
                output_path, findNewMappings(
                        original_kb_name, input_path, original_kb.totalConstants(), sampled_info.constMap
                )
        );
        IntWriter writer = new IntWriter(Paths.get(output_path, sampled_kb_name, CONST_MAP_FILE_NAME).toFile());
        for (int i = 1; i < sampled_info.constMap.length; i++) {    // The first element is always 0, skip
            writer.write(sampled_info.constMap[i]);
        }
        writer.close();
        long time_done = System.currentTimeMillis();
        System.out.printf("Done (%d s)\n", (time_done - time_sampled) / 1000);
        System.out.printf("Total Time: %d s\n", (time_done - time_start) / 1000);
    }

    static protected Set<Integer> loadTypeValues(String kbName, String kbPath) {
        File type_value_file = Paths.get(kbPath, kbName, "TypeValues.dat").toFile();
        Set<Integer> type_values = new HashSet<>();
        try (FileInputStream fis = new FileInputStream(type_value_file)) {
            byte[] buffer = new byte[Integer.BYTES];
            while (Integer.BYTES == fis.read(buffer)) {
                type_values.add(LittleEndianIntIO.byteArray2LeInt(buffer));
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return type_values;
    }

    static protected String[] findNewMappings(
            String originalKbName, String inputPath, int originalConstants, int[] constMap
    ) throws IOException {
        /* Load original mappings */
        String[] original_mapping = new String[originalConstants+1];
        File kb_dir = NumeratedKb.getKbPath(originalKbName, inputPath).toFile();
        File[] map_files = kb_dir.listFiles((dir, name) -> name.matches("map[0-9]+.tsv$"));
        if (null != map_files) {
            /* Sort the files in order */
            String kb_path = kb_dir.getAbsolutePath();
            int idx = 0;
            for (int i = 0; i < map_files.length; i++) {
                File map_file = Paths.get(kb_path, String.format("map%d.tsv", i+NumerationMap.MAP_FILE_NUMERATION_START)).toFile();
                BufferedReader reader = new BufferedReader(new FileReader(map_file));
                String line;
                while (null != (line = reader.readLine())) {
                    idx++;
                    original_mapping[idx] = line;
                }
                reader.close();
            }
        }

        /* Find new mapping */
        String[] new_mapping = new String[constMap.length];
        for (int i = 1; i < constMap.length; i++) {
            new_mapping[i] = original_mapping[constMap[i]];
        }
        return new_mapping;
    }
}
