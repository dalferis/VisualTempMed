import validator
import detector
import converter
import visualizer
import logging
import os

logging.basicConfig(level=logging.DEBUG)

VALIDATION_TYPES = ['xml', 'xmi', 'tml-dtd', 'tml-xsd']

def askDirectoryPath():
    """Asks for a directory, offering known corpus presets."""
    while True:
        path = input("  Directory path: ").strip()
        if not os.path.isdir(path):
            print(f"  Error: directory not found '{path}'")
            continue
        return path


def browseFile(start_dir=None):
    """Interactive directory browser. Returns the selected file path."""
    current = os.path.abspath(start_dir or os.getcwd())

    while True:
        try:
            raw = sorted(os.listdir(current), key=lambda e: (os.path.isfile(os.path.join(current, e)), e.lower()))
        except PermissionError:
            print(f"  No permission to read '{current}'")
            current = os.path.dirname(current)
            continue

        entries = [(os.path.isdir(os.path.join(current, e)), e) for e in raw]

        print(f"\n  [{current}]")
        print("    0. ..")
        for i, (is_dir, name) in enumerate(entries, 1):
            tag = "[DIR]" if is_dir else "     "
            print(f"    {i}. {tag} {name}")

        choice = input(f"  Select [0-{len(entries)}]: ").strip()

        if choice == '0':
            parent = os.path.dirname(current)
            if parent != current:
                current = parent
        elif choice.isdigit() and 1 <= int(choice) <= len(entries):
            is_dir, name = entries[int(choice) - 1]
            full = os.path.join(current, name)
            if is_dir:
                current = full
            else:
                return full
        else:
            print("  Invalid option.")


def askFileOrDirectory(directory_presets=False, start_dir='.'):
    """Asks the user whether to work with a file or a directory, and returns the choice and path."""
    while True:
        print("\n  1. File")
        print("  2. Directory")
        choice = input("  Select [1-2]: ").strip()
        if choice == '1':
            path = browseFile(start_dir=start_dir)
            return 'file', path
        elif choice == '2':
            if directory_presets:
                return 'directory', askDirectoryPath()
            path = input("  Directory path: ").strip()
            if not os.path.isdir(path):
                print(f"  Error: directory not found '{path}'")
                continue
            return 'directory', path
        else:
            print("  Invalid option.")


def askValidationType():
    """Asks the user to pick a validation type. Returns the selected type string."""
    n = len(VALIDATION_TYPES)
    print("\n  Validation type:")
    for i, t in enumerate(VALIDATION_TYPES, 1):
        print(f"    {i}. {t}")
    while True:
        choice = input(f"  Select [1-{n}]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= n:
            return VALIDATION_TYPES[int(choice) - 1]
        print("  Invalid option.")


def menuValidate():
    print("\n=== VALIDATE ===")
    kind, path = askFileOrDirectory(directory_presets=True, start_dir='.\\E3C-Corpus\\data_annotation\\Spanish\\layer1')
    val_type = askValidationType()

    print(f"\nValidating: {path}")
    validator.validate(path, val_type)
    print("\nReport saved to validation_report.txt")


def menuDetect():
    print("\n=== DETECT FORMAT ===")
    path = browseFile()
    fmt = detector.detectFormat(path)
    print(f"\nDetected format for '{path}': {fmt}")


def menuConvert():
    print("\n=== CONVERT ===")
    _, path = askFileOrDirectory(directory_presets=True, start_dir='.\\E3C-Corpus\\data_annotation\\Spanish\\layer1')
    print(f"\nConverting: {path}")
    converter.convert(path)


def menuVisualize():
    print("\n=== VISUALIZE ===")
    path = browseFile(start_dir='.\\E3C-Corpus\\data_annotation\\Spanish\\layer1')
    visualizer.visualize(path)


def main():
    print("\n╔════════════════════════════════╗")
    print("║   Visual Temporal Medical      ║")
    print("╚════════════════════════════════╝")

    options = {
        '1': ('Validate file/directory',  menuValidate),
        '2': ('Detect format',            menuDetect),
        '3': ('Convert file/directory',   menuConvert),
        '4': ('Visualize file',           menuVisualize),
        '0': ('Exit',                     None),
    }

    while True:
        print("\nMain menu:")
        for key, (label, _) in options.items():
            print(f"  {key}. {label}")

        choice = input("\nSelect an option: ").strip()

        if choice == '0':
            break
        elif choice in options:
            _, action = options[choice]
            try:
                action()
            except Exception:
                logging.exception("Error executing option")
        else:
            print("Invalid option. Enter a menu number.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception:
        logging.exception("Error in main")
