package converter;

import sinc2.common.Record;
import sinc2.kb.KbException;
import sinc2.util.LittleEndianIntIO;
import sinc2.util.kb.KbRelation;
import sinc2.util.kb.NumeratedKb;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Paths;
import java.util.*;

/**
 * The base class of all converters. It defines common procedures converting KBs to the numeration format.
 */
public abstract class Converter {

    /** These predicates should be skipped as they do not define factual triples */
    static public Set<String> NON_FACTUAL_PREDICATES = new HashSet<>(List.of(
            "rdfs:domain", "domain",
            "rdfs:range", "range",
            "rdfs:subClassOf", "subClassOf",
            "rdfs:subPropertyOf", "subPropertyOf",
            "rdfs:label", "label",
            "rdfs:comment", "comment",
            "rdfs:isDefinedBy", "isDefinedBy",
            "rdfs:seeAlso", "seeAlso"
    ));
    /** These predicates define type information */
    static protected final String[] TYPE_PREDICATES = new String[]{
            "rdf:type", "type"
    };
    /** The name of the binary file that contains type values */
    static protected final String TYPE_VALUES_FILE_NAME = "TypeValues.dat";

    protected final String outputKbName;
    protected final String outputPath;
    protected NumeratedKb kb;
    protected KbRelation typeRelation;

    public Converter(String outputKbName, String outputPath) {
        this.outputKbName = outputKbName;
        this.outputPath = outputPath;
        kb = new NumeratedKb(outputKbName);
    }

    /**
     * Convert the target KB to the numerated format.
     * @throws ConverterException Conversion failed
     */
    public void convert() throws ConverterException {
        /* Load triples one by one */
        System.out.println("Loading triples ... ");
        long time_start = System.currentTimeMillis();
        Iterator<Triple> iterator = tripleIterator();
        int failed_triples = 0;
        while (iterator.hasNext()) {
            Triple triple = iterator.next();
            if (skipPredicate(triple.pred)) {
                continue;
            }
            try {
                kb.addRecord(triple.pred, new String[]{triple.subj, triple.obj});
            } catch (KbException e) {
                e.printStackTrace();
                failed_triples++;
            }
        }
        if (0 < failed_triples) {
            System.err.printf("%d triples failed to be loaded to numerated KB\n", failed_triples);
        }
        typeRelation = getTypeRelation();
        long time_loaded = System.currentTimeMillis();
        System.out.printf("Done (%d s)\n", (time_loaded - time_start) / 1000);

        /* Re-arrange the order of numerations to make them more concentrate in each relation */
        /* Note: type relation will be handled at the last and will be treated as a single binary relation */
        System.out.println("Rearranging mappings ... ");
        int[] old_2_new = new int[kb.totalMappings()+1];    // Old integer numerations to new
        int next_num = 1;
        List<KbRelation> relations = new ArrayList<>(kb.getRelations());
        relations.sort(Comparator.comparingInt(KbRelation::getId));
        for (KbRelation relation: relations) {  // Re-arrange relations by order
            if (relation == typeRelation) { // Skip the type relation. It will be handled last
                continue;
            }
            for (Record record: relation) {
                for (int arg_idx = 0; arg_idx < record.args.length; arg_idx++) {
                    int old_arg = record.args[arg_idx];
                    if (0 == old_2_new[old_arg]) {
                        old_2_new[old_arg] = next_num;
                        record.args[arg_idx] = next_num;
                        next_num++;
                    } else {
                        record.args[arg_idx] = old_2_new[old_arg];
                    }
                }
            }
        }
        if (null != typeRelation) {
            for (Record record : typeRelation) {
                for (int arg_idx = 0; arg_idx < record.args.length; arg_idx++) {
                    int old_arg = record.args[arg_idx];
                    if (0 == old_2_new[old_arg]) {
                        old_2_new[old_arg] = next_num;
                        record.args[arg_idx] = next_num;
                        next_num++;
                    } else {
                        record.args[arg_idx] = old_2_new[old_arg];
                    }
                }
            }
        }
        if (next_num < old_2_new.length) {
            throw new ConverterException(String.format(
                    "Numeration rearrange error: %d numerations expected, but %d rearranged", old_2_new.length - 1, next_num - 1
            ));
        }
        kb.rearrangeMapping(old_2_new);
        long time_rearranged = System.currentTimeMillis();
        System.out.printf("Done (%d s)\n", (time_rearranged - time_loaded) / 1000);

        /* Dump the KB */
        /* Type values will be dumped to a single file "TypeValues.dat" */
        System.out.println("Dumping ... ");
        try {
            kb.dump(outputPath);
        } catch (IOException e) {
            e.printStackTrace();
        }
        if (null != typeRelation) {
            File file = Paths.get(NumeratedKb.getKbPath(outputKbName, outputPath).toString(), TYPE_VALUES_FILE_NAME).toFile();
            try (FileOutputStream fos = new FileOutputStream(file)) {
                for (Record record : typeRelation) {
                    fos.write(LittleEndianIntIO.leInt2ByteArray(record.args[1]));
                }
            } catch (IOException e) {
                System.err.println("Type value file creation failed: " + file.getAbsolutePath());
                e.printStackTrace();
            }
        }
        long time_dumped = System.currentTimeMillis();
        System.out.printf("Done (%d s)\n", (time_dumped - time_rearranged) / 1000);
        System.out.printf("Totoal Time: %d s\n", (time_dumped - time_start) / 1000);
    }

    /**
     * Get an iterator of triples in the original KB.
     */
    abstract protected Iterator<Triple> tripleIterator() throws ConverterException;

    /**
     * Check if the predicate should be skipped.
     */
    protected boolean skipPredicate(String predicate) {
        return NON_FACTUAL_PREDICATES.contains(predicate);
    }

    /**
     * Find the type relation in the KB. The type relation is found by matching the possible names of the relation indicated
     * in "TYPE_PREDICATES".
     * @return If not found, NULL is returned.
     */
    protected KbRelation getTypeRelation() {
        for (String type_predicate: TYPE_PREDICATES) {
            KbRelation type_relation = kb.getRelation(type_predicate);
            if (null != type_relation) {
                return type_relation;
            }
        }
        return null;
    }
}
