package converter.impl;

import converter.Converter;
import converter.Triple;

import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

/**
 * Converter that matches the YAGO 1 structure.
 */
public class Yago1Converter extends Converter {

    /** These are predicates in YAGO 1 that should be skipped */
    protected static final Set<String> NON_FACTUAL_PREDICATES = new HashSet<>(List.of(
            "describes",
            "foundIn",
            "extractedBy",
            "context"
    ));

    protected final String kbPath;

    public Yago1Converter(String kbPath, String outputKbName, String outputPath) {
        super(outputKbName, outputPath);
        this.kbPath = kbPath;
    }

    @Override
    protected Iterator<Triple> tripleIterator() {
        return new Yago1Iterator(kbPath);
    }

    @Override
    protected boolean skipPredicate(String predicate) {
        return false;
    }
}
