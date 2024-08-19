import unittest
from plasmapdf.models.PdfDataLayer import makePdfTranslationLayerFromPawlsTokens
from plasmapdf.models.types import TextSpan, SpanAnnotation, PawlsPagePythonType
import pandas as pd

class TestPdfDataLayer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Sample PAWLS tokens for testing
        cls.pawls_tokens: list[PawlsPagePythonType] = [
            {
                "page": {"width": 612, "height": 792, "index": 0},
                "tokens": [
                    {"x": 72, "y": 72, "width": 50, "height": 12, "text": "This"},
                    {"x": 130, "y": 72, "width": 20, "height": 12, "text": "is"},
                    {"x": 158, "y": 72, "width": 40, "height": 12, "text": "a"},
                    {"x": 206, "y": 72, "width": 60, "height": 12, "text": "sample"},
                    {"x": 274, "y": 72, "width": 50, "height": 12, "text": "PDF"},
                    {"x": 332, "y": 72, "width": 80, "height": 12, "text": "document."}
                ]
            }
        ]
        cls.pdf_data_layer = makePdfTranslationLayerFromPawlsTokens(cls.pawls_tokens)

    def test_get_raw_text_from_span(self):
        span = TextSpan(id="1", start=0, end=29, text="This is a sample PDF document")
        raw_text = self.pdf_data_layer.get_raw_text_from_span(span)
        self.assertEqual(raw_text, "This is a sample PDF document")

    def test_convert_doc_span_to_opencontract_annotation_json(self):
        span = TextSpan(id="1", start=0, end=29, text="This is a sample PDF document")
        annotation_json = self.pdf_data_layer.convert_doc_span_to_opencontract_annotation_json(span)
        self.assertIsInstance(annotation_json, dict)
        self.assertIn(0, annotation_json)  # Check if page 0 is in the annotation
        self.assertIn('bounds', annotation_json[0])
        self.assertIn('rawText', annotation_json[0])
        self.assertIn('tokensJsons', annotation_json[0])

    def test_split_span_on_pages(self):
        span = TextSpan(id="1", start=0, end=29, text="This is a sample PDF document")
        page_aware_spans = self.pdf_data_layer.split_span_on_pages(span)
        print(page_aware_spans)
        self.assertEqual(len(page_aware_spans), 1)  # Only one page in our sample
        self.assertEqual(page_aware_spans[0]['page'], 0)
        self.assertEqual(page_aware_spans[0]['text'], "This is a sample PDF document")

    def test_create_opencontract_annotation_from_span(self):
        span = TextSpan(id="1", start=0, end=29, text="This is a sample PDF document")
        span_annotation = SpanAnnotation(span=span, annotation_label="SAMPLE_TEXT")
        oc_annotation = self.pdf_data_layer.create_opencontract_annotation_from_span(span_annotation)
        self.assertIsInstance(oc_annotation, dict)
        self.assertEqual(oc_annotation['annotationLabel'], "SAMPLE_TEXT")
        self.assertEqual(oc_annotation['rawText'], "This is a sample PDF document")
        self.assertEqual(oc_annotation['page'], 0)

    def test_doc_text(self):
        self.assertEqual(self.pdf_data_layer.doc_text, "This is a sample PDF document.")

    def test_human_friendly_full_text(self):
        self.assertEqual(self.pdf_data_layer.human_friendly_full_text, "This is a sample PDF document.")

    def test_page_dataframe(self):
        self.assertIsInstance(self.pdf_data_layer.page_dataframe, pd.DataFrame)
        self.assertEqual(len(self.pdf_data_layer.page_dataframe), 1)  # One page

    def test_tokens_dataframe(self):
        self.assertIsInstance(self.pdf_data_layer.tokens_dataframe, pd.DataFrame)
        self.assertEqual(len(self.pdf_data_layer.tokens_dataframe), 6)  # 6 tokens

    def test_page_tokens(self):
        self.assertIn(0, self.pdf_data_layer.page_tokens)
        self.assertEqual(len(self.pdf_data_layer.page_tokens[0]), 6)  # 6 tokens on page 0

if __name__ == '__main__':
    unittest.main()