import json
import os
import unittest
from typing import List

import pandas as pd

from plasmapdf.models.PdfDataLayer import build_translation_layer
from plasmapdf.models.types import (
    PawlsPagePythonType,
    SpanAnnotation,
    TextSpan,
)


class TestPdfDataLayer(unittest.TestCase):
    def setUp(self) -> None:
        # Load test fixtures
        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "pawls.json")
        with open(fixture_path, "r") as f:
            self.pawls_full = json.load(f)
            self.pawls_page_0 = self.pawls_full[0]

        # Original test data
        self.pawls_tokens: List[PawlsPagePythonType] = [
            {
                "page": {"width": 612, "height": 792, "index": 0},
                "tokens": [
                    {"x": 72, "y": 72, "width": 50, "height": 12, "text": "This"},
                    {"x": 130, "y": 72, "width": 20, "height": 12, "text": "is"},
                    {"x": 158, "y": 72, "width": 40, "height": 12, "text": "a"},
                    {"x": 206, "y": 72, "width": 60, "height": 12, "text": "sample"},
                    {"x": 274, "y": 72, "width": 50, "height": 12, "text": "PDF"},
                    {"x": 332, "y": 72, "width": 80, "height": 12, "text": "document."},
                ],
            }
        ]

        # Create both data layers
        self.made_up_pdf_data_layer = build_translation_layer(self.pawls_tokens)
        self.pdf_page_0_data_layer = build_translation_layer([self.pawls_page_0])
        self.pdf_full_data_layer = build_translation_layer(self.pawls_full)

    def test_get_raw_text_from_span(self) -> None:
        span = TextSpan(id="1", start=0, end=29, text="This is a sample PDF document")
        raw_text = self.made_up_pdf_data_layer.get_raw_text_from_span(span)
        self.assertEqual(raw_text, "This is a sample PDF document")

    def test_convert_doc_span_to_opencontract_annotation_json(self) -> None:
        span = TextSpan(id="1", start=0, end=29, text="This is a sample PDF document")
        annotation_json = self.made_up_pdf_data_layer.convert_doc_span_to_opencontract_annotation_json(
            span
        )
        self.assertIsInstance(annotation_json, dict)
        self.assertIn(0, annotation_json)  # Check if page 0 is in the annotation
        self.assertIn("bounds", annotation_json[0])
        self.assertIn("rawText", annotation_json[0])
        self.assertIn("tokensJsons", annotation_json[0])

    def test_split_span_on_pages(self) -> None:
        span = TextSpan(id="1", start=0, end=29, text="This is a sample PDF document")
        page_aware_spans = self.made_up_pdf_data_layer.split_span_on_pages(span)
        print(page_aware_spans)
        self.assertEqual(len(page_aware_spans), 1)  # Only one page in our sample
        self.assertEqual(page_aware_spans[0]["page"], 0)
        self.assertEqual(page_aware_spans[0]["text"], "This is a sample PDF document")

    def test_create_opencontract_annotation_from_span(self) -> None:
        span = TextSpan(id="1", start=0, end=29, text="This is a sample PDF document")
        span_annotation = SpanAnnotation(span=span, annotation_label="SAMPLE_TEXT")
        oc_annotation = (
            self.made_up_pdf_data_layer.create_opencontract_annotation_from_span(
                span_annotation
            )
        )
        self.assertIsInstance(oc_annotation, dict)
        self.assertEqual(oc_annotation["annotationLabel"], "SAMPLE_TEXT")
        self.assertEqual(oc_annotation["rawText"], "This is a sample PDF document")
        self.assertEqual(oc_annotation["page"], 0)

    def test_doc_text(self) -> None:
        self.assertEqual(
            self.made_up_pdf_data_layer.doc_text, "This is a sample PDF document."
        )

    def test_human_friendly_full_text(self) -> None:
        self.assertEqual(
            self.made_up_pdf_data_layer.human_friendly_full_text,
            "This is a sample PDF document.",
        )

    def test_page_dataframe(self) -> None:
        self.assertIsInstance(self.made_up_pdf_data_layer.page_dataframe, pd.DataFrame)
        self.assertEqual(len(self.made_up_pdf_data_layer.page_dataframe), 1)  # One page

    def test_tokens_dataframe(self) -> None:
        self.assertIsInstance(
            self.made_up_pdf_data_layer.tokens_dataframe, pd.DataFrame
        )
        self.assertEqual(
            len(self.made_up_pdf_data_layer.tokens_dataframe), 6
        )  # 6 tokens

    def test_page_tokens(self) -> None:
        self.assertIn(0, self.made_up_pdf_data_layer.page_tokens)
        self.assertEqual(
            len(self.made_up_pdf_data_layer.page_tokens[0]), 6
        )  # 6 tokens on page 0

    def test_get_raw_text_from_span_eton(self) -> None:
        """Test that a span containing 'Eton' at position 533-537 is correctly retrieved"""
        span = TextSpan(id="2", start=533, end=537, text="ETON")
        raw_text = self.pdf_page_0_data_layer.get_raw_text_from_span(span)
        self.assertEqual(raw_text, "ETON")

        span_annotation = SpanAnnotation(span=span, annotation_label="REDACT")
        oc_annotation = (
            self.pdf_page_0_data_layer.create_opencontract_annotation_from_span(
                span_annotation
            )
        )
        print(f"oc_annotation: {oc_annotation}")

        oc_annotation_idx = oc_annotation["annotation_json"][0]["tokensJsons"][0][  # type: ignore
            "tokenIndex"
        ]

        # Verify the tokens exist in the underlying data layer
        tokens_df = self.pdf_page_0_data_layer.tokens_dataframe
        print(f"~~~ tokens_df: {tokens_df}")
        matching_tokens = tokens_df[
            (tokens_df["Char_Start"] <= 537) & (tokens_df["Char_End"] >= 533)
        ]
        self.assertFalse(matching_tokens.empty, "Should find tokens for 'Eton'")

        match_idx = matching_tokens.iloc[0]["Token_Id"]
        self.assertEqual(match_idx, oc_annotation_idx)

    def test_page_breaks(self) -> None:
        """
        Ensures we can detect text spans that span across page boundaries.

        1. For each page in pawls_full (except the last), grab the last three tokens of the current page
           and the first three tokens of the next page, joined by spaces, but using the data layer's
           page_tokens text (which is post-processed).
        2. Locate that substring in the pdf_full_data_layer.doc_text to find the character start/end.
        3. Create a SpanAnnotation from this substring and generate an annotation
           via create_opencontract_annotation_from_span.
        4. Assert that the resulting annotation_json has entries for both pages (total of 2).
        """
        doc_text: str = self.pdf_full_data_layer.doc_text

        for page_index in range(len(self.pawls_full) - 1):
            current_page_tokens = self.pdf_full_data_layer.page_tokens[page_index]
            next_page_tokens = self.pdf_full_data_layer.page_tokens[page_index + 1]

            # Skip if a page doesn't have enough tokens
            if len(current_page_tokens) < 3 or len(next_page_tokens) < 3:
                continue

            # Grab the post-processed token text from the data layer
            last_three_current = [tok["text"] for tok in current_page_tokens[-3:]]
            first_three_next = [tok["text"] for tok in next_page_tokens[:3]]
            joined_text = " ".join(last_three_current + first_three_next)

            print(
                f"Look for substring that breaks on pages {page_index}-{page_index + 1}: {joined_text}"
            )

            start_ix: int = doc_text.find(joined_text)
            self.assertNotEqual(
                start_ix,
                -1,
                f"Expected to find substring '{joined_text}' across pages {page_index}-{page_index + 1}",
            )
            end_ix: int = start_ix + len(joined_text)

            span = TextSpan(
                id=f"page_break_span_{page_index}",
                start=start_ix,
                end=end_ix,
                text=joined_text,
            )
            span_annotation = SpanAnnotation(
                span=span, annotation_label="PAGE_BREAK_TEST"
            )
            oc_annotation = (
                self.pdf_full_data_layer.create_opencontract_annotation_from_span(
                    span_annotation
                )
            )

            # We expect two-page entries in annotation_json because the span crosses a page boundary
            self.assertEqual(
                len(oc_annotation["annotation_json"]),
                2,
                f"Annotation should have 2 pages in annotation_json for break across pages {page_index}-{page_index + 1}",
            )


if __name__ == "__main__":
    unittest.main()
