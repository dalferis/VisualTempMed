# VisualTempMed

Medical Timeline Visualizer.

Desktop application that converts temporally annotated medical corpora from the **E3C** format (XMI/UIMA) to the **TimeML** (TML) format and visualizes them as an interactive temporal graph or as annotated text with linked mentions.

## Features

- **Load** TimeML (`.tml`) and E3C (`.xml`) files, with automatic format detection.
- **Convert** E3C -> TimeML following the translation table documented in `doc/esquema_traduccion_E3C_TimeML.txt`.
- **Validate** TimeML files structurally (XSD `TimeML_1.2.4`) and semantically (TimeML specification).
- **Optional inference** of synthetic TLINKs from comparable dates between TIMEX3 mentions.
- **Time view**: graph with events and instances ordered chronologically left to right; simultaneous mentions stack vertically.
- **Text view**: source text with inline annotations and routed edges between mentions.
- Attributes panel to inspect nodes and links, including the DCT (Document Creation Time).
- Visual differentiation of annotated TLINKs, TLEX-suggested TLINKs, and date-inferred TLINKs.

## Requirements

- Python 3.10 or later.
- Dependencies listed in `requirements.txt`: `dkpro-cassis`, `lxml`, `xmlschema`, `python-dateutil`, `PySide6`, `z3-solver`, `networkx`.

## Installation

```
pip install -r requirements.txt
```

## Running

```
python mainWindow.py
```

## Layout

| File / folder | Purpose |
|---|---|
| `mainWindow.py` | GUI entry point (PySide6); File / Tools / Options / View / Help menus. |
| `converter.py` | E3C -> TimeML conversion (`convertFile`, `convertContent`). |
| `validator.py` | XML / TML-XSD / TML-spec validation (`validateFile`, `validateContent`). |
| `detector.py` | Format detection (`detectFormatFile`, `detectFormatContent`, `FileFormat` enum). |
| `dateLinks.py` | Inference of synthetic TLINKs from datable TIMEX3 mentions. |
| `dataModel.py` | Internal data model. |
| `timeView.py` / `textView.py` / `sceneItems.py` | Visualization views and scene items. |
| `pytlex_core/` | Third-party dependency (PyTLEX): partitioning, TLEX, Z3 TCSP solver. |
| `XSD/` | XSD / DTD schemas; the active one is `TimeML_1.2.4.xsd`. |
| `E3C-Corpus/` | E3C input corpus (English and Spanish, layer1). |
| `pytlex_data/` | TimeBank reference corpus. |
| `unit_tests/` | Unit tests (pytest). |

## Tests

```
pytest unit_tests/
```
