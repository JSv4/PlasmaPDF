# PlasmaPDF Quick Start Guide

PlasmaPDF is a Python library for converting from txt spans to x-y positioned tokens in the PAWLs format. It is a utility library used in OpenContracts and PdfRedactor. 

## Installation

To install PlasmaPDF, use pip:

```
pip install plasmapdf
```

## Understanding PdfDataLayer: A Bridge Between Span and PDF Coordinates
The PlasmaPDF's PdfDataLayer is a solution to a complex problem: maintaining perfect synchronization between plain text spans and their physical locations in PDFs. Let's break it down:

### Core Concept / Use Case
PdfDataLayer is designed to keep span-based annotations consistent with the underlying PDF tokens such that's it's easy to convert between the two. In today's LLM-powered world, one obvious use case is converting LLM-generated span coordinates to PDF x,y coordinates for annotations and redactions. This requires using the OCR tokens as the source of truth and generating the text layer from the tokens with consistent preprocessing.

### Input Requirements

#### 1. PAWLS Token Layout

The fundamental building-block of our translation layer is the PAWLS token - a format we originally adopted from Allen AI's PAWLS project. Check out detailed typing in [types](/plasmapdf/models/types.py).

**PAWLs Token Example:**
```python
pawls_tokens = [
    {
        "page": {"width": 612, "height": 792, "index": 0},
        "tokens": [
            {"x": 72, "y": 72, "width": 50, "height": 12, "text": "Hello"},
            {"x": 130, "y": 72, "width": 50, "height": 12, "text": "World"}
        ]
    }
]
```
This represents the foundational "source of truth" - the actual positions of text on PDF pages.

#### 2. Derived DataFrames
We then use pandas DataFrames to create efficient indices:

```python
# Page DataFrame tracks character ranges per page
page_df = pd.DataFrame([
    {"Page": 0, "Start": 0, "End": 500},
    {"Page": 1, "Start": 501, "End": 1000}
])

# Token DataFrame maps each token to its character position
token_df = pd.DataFrame([
    {"Page": 0, "Token_Id": 0, "Char_Start": 0, "Char_End": 5},
    {"Page": 0, "Token_Id": 1, "Char_Start": 6, "Char_End": 11}
])
```

### Design Decisions

1. **Character-Based Indexing**
   - Uses character positions as the universal coordinate system
   - Makes it trivial to map between text spans and token positions
   - Enables precise multi-page span handling

2. **Token-First Architecture**
   - Builds text from tokens rather than trying to match text to tokens
   - Guarantees **perfect** alignment between text and PDF coordinates, so long as you use `doc_text` property provided by `PdfDataLayer` to search for spans.
   - Prevents common OCR/text alignment issues

## Why it's Useful

`PdfDataLayer` solves several thorny problems:

1. **Bidirectional Mapping**: Seamlessly converts between text positions and PDF coordinates
2. **Multi-Page Handling**: Correctly handles spans that cross page boundaries
3. **OCR Normalization**: Manages common OCR artifacts and character variations
4. **Efficient Lookups**: Uses DataFrame indices for fast position queries
5. **Clean API**: Provides intuitive methods for common operations

This addresses some serious and common real-world document processing challenges and provides a solution that's both powerful and practical.

## Basic Usage

### 1. Importing the Library

Start by importing the necessary components:

```python
from plasmapdf.models.PdfDataLayer import build_translation_layer
from plasmapdf.models.types import TextSpan, SpanAnnotation, PawlsPagePythonType
```

### 2. Creating a PdfDataLayer

The core of plasmaPDF is the `PdfDataLayer` class. You create an instance of this class using
the `build_translation_layer` function:

```python
pawls_tokens: list[PawlsPagePythonType] = [
    {
        "page": {"width": 612, "height": 792, "index": 0},
        "tokens": [
            {"x": 72, "y": 72, "width": 50, "height": 12, "text": "Hello"},
            {"x": 130, "y": 72, "width": 50, "height": 12, "text": "World"}
        ]
    }
]

pdf_data_layer = build_translation_layer(pawls_tokens)
```

### 3. Working with Text Spans

You can extract raw text from a span in the document:

```python
span = TextSpan(id="1", start=0, end=11, text="Hello World")
raw_text = pdf_data_layer.get_raw_text_from_span(span)
print(raw_text)  # Output: "Hello World"
```

### 4. Creating Annotations

To create an annotation:

```python
span_annotation = SpanAnnotation(span=span, annotation_label="GREETING")
oc_annotation = pdf_data_layer.create_opencontract_annotation_from_span(span_annotation)
```

### 5. Accessing Document Information

You can access various pieces of information about the document:

```python
print(pdf_data_layer.doc_text)  # Full document text
print(pdf_data_layer.human_friendly_full_text)  # Human-readable version of the text
print(pdf_data_layer.page_dataframe)  # DataFrame with page information
print(pdf_data_layer.tokens_dataframe)  # DataFrame with token information
```

## Development Setup

PlasmaPDF uses `hatch` for environment and development workflow management. Here's how to get started:

### 1. Install Hatch

First, install hatch globally:

```bash
pip install hatch
```

### 2. Development Environment

Hatch automatically manages virtual environments for you. To activate the development environment:

```bash
hatch shell dev
```

### 3. Running Tests

PlasmaPDF uses pytest for testing. To run tests:

```bash
hatch run dev:pytest
```

For tests with coverage:

```bash
hatch run dev:pytest --cov
```

### 4. Code Quality Tools

PlasmaPDF comes with several code quality tools configured:

#### Formatting
To format your code using `black` and `isort`:

```bash
hatch run dev:format
```

#### Linting
To run flake8 linting:

```bash
hatch run dev:lint
```

#### Type Checking
To run mypy type checking:

```bash
hatch run types:check
```

### 5. Environment Details

PlasmaPDF defines several hatch environments in `pyproject.toml`:

- `dev`: Main development environment with testing and formatting tools
- `types`: Environment for type checking with mypy

Each environment has its own dependencies and scripts defined in `pyproject.toml`.

### 6. Code Style

The project follows these standards:
- Line length: 88 characters (Black default)
- Python version: 3.8+
- Strict type checking with mypy
- Black code style
- Isort for import sorting (configured to be compatible with Black)

## Advanced Usage

### Working with Multi-Page Documents

PlasmaPDF can handle multi-page documents. When you create the `PdfDataLayer`, make sure to include tokens for all
pages:

```python
multi_page_pawls_tokens = [
    {
        "page": {"width": 612, "height": 792, "index": 0},
        "tokens": [...]
    },
    {
        "page": {"width": 612, "height": 792, "index": 1},
        "tokens": [...]
    }
]

pdf_data_layer = build_translation_layer(multi_page_pawls_tokens)
```

### Splitting Spans Across Pages

If you have a span that potentially crosses page boundaries, you can split it:

```python
long_span = TextSpan(id="2", start=0, end=1000, text="...")
page_aware_spans = pdf_data_layer.split_span_on_pages(long_span)
```

### Creating OpenContracts Annotations

To create an annotation in the OpenContracts format:

```python
span = TextSpan(id="3", start=0, end=20, text="Important clause here")
span_annotation = SpanAnnotation(span=span, annotation_label="IMPORTANT_CLAUSE")
oc_annotation = pdf_data_layer.create_opencontract_annotation_from_span(span_annotation)
```

## Utility Functions

PlasmaPDF includes utility functions for working with job results:

```python
from plasmapdf.utils.utils import package_job_results_to_oc_generated_corpus_type

# Assume you have job_results, possible_span_labels, possible_doc_labels, 
# possible_relationship_labels, and suggested_label_set

corpus = package_job_results_to_oc_generated_corpus_type(
    job_results,
    possible_span_labels,
    possible_doc_labels,
    possible_relationship_labels,
    suggested_label_set
)
```

This function packages job results into the OpenContracts corpus format.

## Testing

PlasmaPDF comes with a suite of unit tests. You can run these tests to ensure everything is working correctly:

```
hatch test
```

This will run all the tests in the `tests` directory.

## Conclusion

This quick start guide covers the basics of using PlasmaPDF. For more detailed information, refer to the tests or explore the source code. If you encounter any issues or have questions, please refer to the project's issue tracker or documentation.
