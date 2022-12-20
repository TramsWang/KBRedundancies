package converter;

import converter.impl.Yago1Converter;

public class Main {
    public static void main(String[] args) throws ConverterException {
        if (4 != args.length) {
            System.out.println("Usage: <Converter Name> <Input Path> <Output Path> <Output KB Name>");
            return;
        }

        final String converter_name = args[0];
        final String intput_path = args[1];
        final String output_path = args[2];
        final String output_kb_name = args[3];

        Converter converter;
        switch (converter_name) {
            case "YAGO1":
                converter = new Yago1Converter(intput_path, output_kb_name, output_path);
                break;
            default:
                throw new ConverterException("Unknown converter: " + converter_name);
        }
        converter.convert();
    }
}
