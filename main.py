import argparse
import validator
import detector
import converter
import visualizer

def main():
    parser = argparse.ArgumentParser(description='Visual Temporal Medical')

    subparser = parser.add_subparsers(dest='subcommand')

    parser_val = subparser.add_parser('validate', help='Validate XML files against XSD schema')
    parser_val_group = parser_val.add_mutually_exclusive_group(required=True)
    parser_val_group.add_argument('--file', '-f', nargs=1, help='Input file for analyse')
    parser_val_group.add_argument('--directory', '-d', nargs=1, help='Directory for analyse its files')
    parser_val.add_argument('--type', '-t', nargs=1, required=True, choices=['xml', 'xml-dtd', 'xml-xsd', 'xmi', 'tml', 'e3c'], help='Type of file for validation')

    parser_det = subparser.add_parser('detect', help='Detect files format')
    parser_det_group = parser_det.add_mutually_exclusive_group(required=True)
    parser_det_group.add_argument('--file', '-f', nargs=1, help='Input file for detect format')
    parser_det_group.add_argument('--directory', '-d', nargs=1, help='Directory for detect format of its files')

    parser_con = subparser.add_parser('convert', help='Convert to another format')
    parser_con_group = parser_con.add_mutually_exclusive_group(required=True)
    parser_con_group.add_argument('--file', '-f', nargs=1, help='Input file for convert')
    parser_con_group.add_argument('--directory', '-d', nargs=1, help='Directory for convert its files')
    parser_con.add_argument('--typesystem', '-t', nargs=1, required=False, default='E3C-Corpus\\TypeSystem.xml', help='Typesystem file')

    parser_vis = subparser.add_parser('visualize', help='Visualize')
    parser_vis.add_argument('--file', '-f', nargs=1, required=True, help='Input file for convert')

    try:
        args = parser.parse_args()
    except:
        return

    if args.subcommand == 'validate':
        if args.file:
            inputFile = args.file[0]
            print(f"Validating file: {inputFile}")
            result = validator.validateFile(inputFile, args.type[0])
            print("\n".join(result[1:]))
            with open("validation_report.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(result[1:]))
        elif args.directory:
            inputDir = args.directory[0]
            print(f"Validating folder: {inputDir}")
            result = validator.validateDirectory(inputDir, args.type[0])
            print("\n".join(result))
            with open("validation_report.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(result))
    elif args.subcommand == 'detect':
        if args.file:
            inputFile = args.file[0]
            format = detector.detectFormatInFile(inputFile)
            print(f"Detected format for file {inputFile}: {format}")
        elif args.directory:
            inputDir = args.directory[0]
            formats = detector.detectFormatInDirectory(inputDir)
            print(f"Detecting formats in directory: {inputDir}")
            for file, format in formats.items():
                print(f"File: {file}, Format: {format}")
    elif args.subcommand == 'convert':
        if args.file:
            inputFile = args.file[0]
            print(f"Converting file: {inputFile}")
            newContent = converter.convertFile(inputFile, args.typesystem[0] if isinstance(args.typesystem, list) else args.typesystem)
            print(newContent)
        elif args.directory:
            inputDir = args.directory[0]
            print(f"Converting files in directory: {inputDir}")
            # for file, format in formats.items():
            #     newContent = converter.convertFile(inputFile, args.typesystem[0])
            #     print(newContent)
    elif args.subcommand == "visualize":
        visualizer.visualize(args.file[0])

        
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")