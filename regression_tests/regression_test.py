"""
Regression test over the full E3C corpus.

Walks E3C-Corpus/data_annotation/<Language>/layer1/*.xml and runs each
file through converter.convertContent (which internally validates the
TimeML against XSD + spec). Reports OK/FAIL counts per language and,
with -v, the error of every failing file.

Run from the project root:
    python regression_tests/regression_test.py
    python regression_tests/regression_test.py -v
    python regression_tests/regression_test.py --language English
"""
import argparse
import os
import sys
import time

# Make the script runnable from the project root regardless of cwd.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

os.chdir(_PROJECT_ROOT)  # typesystem path inside converter is relative

import converter
import detector


CORPUS_ROOT = os.path.join("E3C-Corpus", "data_annotation")
LANGUAGES = ["Basque", "English", "French", "Italian", "Spanish"]


def iterCorpusFiles(languages):
    for lang in languages:
        layer = os.path.join(CORPUS_ROOT, lang, "layer1")
        if not os.path.isdir(layer):
            continue
        for name in sorted(os.listdir(layer)):
            if name.endswith(".xml"):
                yield lang, os.path.join(layer, name)


def runRegression(languages, verbose):
    results = {lang: {"ok": 0, "fail": 0, "skipped": 0, "errors": []} for lang in languages}
    total_files = 0
    t0 = time.perf_counter()

    for lang, path in iterCorpusFiles(languages):
        total_files += 1
        with open(path, encoding="utf-8") as f:
            content = f.read()
        if detector.detectFormatContent(content) != detector.FileFormat.E3C:
            results[lang]["skipped"] += 1
            continue
        outcome = converter.convertContent(content)
        if outcome[0]:
            results[lang]["ok"] += 1
        else:
            results[lang]["fail"] += 1
            results[lang]["errors"].append((path, outcome[1:]))

    elapsed = time.perf_counter() - t0
    return results, total_files, elapsed


def printSummary(results, total_files, elapsed, verbose):
    print()
    print(f"{'Language':<10} {'OK':>6} {'FAIL':>6} {'Skipped':>8} {'Total':>6}")
    print("-" * 42)
    total_ok = total_fail = total_skipped = 0
    for lang, stats in results.items():
        ok = stats["ok"]
        fail = stats["fail"]
        skipped = stats["skipped"]
        total = ok + fail + skipped
        if total == 0:
            continue
        print(f"{lang:<10} {ok:>6} {fail:>6} {skipped:>8} {total:>6}")
        total_ok += ok
        total_fail += fail
        total_skipped += skipped
    print("-" * 42)
    print(f"{'TOTAL':<10} {total_ok:>6} {total_fail:>6} {total_skipped:>8} {total_files:>6}")
    print()
    print(f"Elapsed: {elapsed:.1f} s")

    if verbose and total_fail > 0:
        print()
        print("Failing files:")
        for lang, stats in results.items():
            for path, errors in stats["errors"]:
                print(f"  [{lang}] {path}")
                for err in errors:
                    print(f"      -> {err}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--language", "-l", action="append",
                   choices=LANGUAGES,
                   help="Restrict to one or more languages (repeatable). "
                        "Default: all.")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Print the error of every failing file.")
    args = p.parse_args()

    languages = args.language if args.language else LANGUAGES
    results, total_files, elapsed = runRegression(languages, args.verbose)
    printSummary(results, total_files, elapsed, args.verbose)
    sys.exit(0 if all(s["fail"] == 0 for s in results.values()) else 1)


if __name__ == "__main__":
    main()
