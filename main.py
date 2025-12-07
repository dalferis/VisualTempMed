import argparse
import validator
import detector
import xml.etree.ElementTree as ET
import sys
import os
from pytlex_core.data import Event, Graph, Instance, TimeX, Signal, Link
from pytlex_core.algorithms import TLEX, TimeMLParser

def prettyPrintXml(xmlfile: str):
    try:
        tree = ET.parse(xmlfile)
    except:
        print("Error parsing XML file.")

    elementTree = ET.ElementTree(tree.getroot())
    ET.indent(elementTree, space="  ", level=0)
    print(ET.tostring(tree.getroot(), encoding="unicode"))

def main():
    parser = argparse.ArgumentParser(description='Visual Temporal Medical')

    subparser = parser.add_subparsers(dest='subcommand')

    parser_val = subparser.add_parser('validate', help='Validate XML files against XSD schema')
    parser_val_group = parser_val.add_mutually_exclusive_group(required=True)
    parser_val_group.add_argument('--file', '-f', nargs=1, help='Input file for analyse')
    parser_val_group.add_argument('--directory', '-d', nargs=1, help='Directory for analyse its files')
    parser_val.add_argument('--schema', '-s', nargs=1, required=True, help='Schema for validation')

    parser_det = subparser.add_parser('detect', help='Detect files format')
    parser_det_group = parser_det.add_mutually_exclusive_group(required=True)
    parser_det_group.add_argument('--file', '-f', nargs=1, help='Input file for detect format')
    parser_det_group.add_argument('--directory', '-d', nargs=1, help='Directory for detect format of its files')

    try:
        args = parser.parse_args()
    except:
        return

    if args.subcommand == 'validate':
        if args.file:
            inputFile = args.file[0]
            print(f"Validating file: {inputFile}")
            result = validator.validateFile(inputFile, args.schema[0])
            print("\n".join(result))
            with open("validation_report.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(result))
        elif args.directory:
            inputDir = args.directory[0]
            print(f"Validating folder: {inputDir}")
            result = validator.validateDirectory(inputDir, args.schema[0])
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


    # inputFile = 'pytlex_data\\TimeBankCorpus\\wsj_0006.tml'
    # #inputFile = 'E3C-Corpus\\data_annotation\\Spanish\\layer1\\ES100001.xml'
    # prettyPrintXml(inputFile)
    # #content = TimeMLParser.read_file_data(inputFile)

    # graph = Graph.Graph(filepath = inputFile)
    # tlex = TLEX.TLEX(graph = graph)
    # print(tlex.partitions)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")