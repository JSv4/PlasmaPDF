# PlasmaPDF Quick Start Guide

PlasmaPDF is a Python library for converting from txt spans to x-y positioned tokens in the PAWLs format. It is a utility library used in OpenContracts and PdfRedactor. 

## Installation

To install PlasmaPDF, use pip:

```
pip install plasmapdf
```

## Basic Usage

### 1. Importing the Library

Start by importing the necessary components:

```python
from plasmapdf.models.PdfDataLayer import build_translation_layer
from plasmapdf.models.types import TextSpan, SpanAnnotation, PawlsPagePythonType
```

### 2. Creating a PdfDataLayer

The core of plasmaPDF is the `PdfDataLayer` class. You create an instance of this class using
the `makePdfTranslationLayerFromPawlsTokens` function:

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

pdf_data_layer = makePdfTranslationLayerFromPawlsTokens(pawls_tokens)
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

pdf_data_layer = makePdfTranslationLayerFromPawlsTokens(multi_page_pawls_tokens)
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

This quick start guide covers the basics of using PlasmaPDF. For more detailed information, refer to the full
documentation or explore the source code. If you encounter any issues or have questions, please refer to the project's
issue tracker or documentation.
