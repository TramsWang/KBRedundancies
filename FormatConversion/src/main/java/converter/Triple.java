package converter;

/**
 * The triple structure
 */
public class Triple {
    public final String subj;
    public final String pred;
    public final String obj;

    public Triple(String subj, String pred, String obj) {
        this.subj = subj;
        this.pred = pred;
        this.obj = obj;
    }
}
