import unittest
from plasmapdf.utils.utils import package_job_results_to_oc_generated_corpus_type, is_dict_instance_of_typed_dict
from plasmapdf.models.types import (
    OpenContractsGeneratedCorpusPythonType,
    LabelType
)


class TestPackageJobResults(unittest.TestCase):

    def setUp(self):
        self.job_results = {
            1: {
                "doc_id": 1,
                "task_status": "SUCCESS",
                "task_message": "Document processed successfully",
                "annotations": {
                    "doc_labels": ["CONTRACT"],
                    "labelled_text": [
                        {
                            "id": "1",
                            "annotationLabel": "PARTY",
                            "rawText": "Company A",
                            "page": 1,
                            "annotation_json": {
                                1: {
                                    "bounds": {"top": 100, "bottom": 120, "left": 50, "right": 150},
                                    "rawText": "Company A",
                                    "tokensJsons": [{"pageIndex": 1, "tokenIndex": 1}]
                                }
                            }
                        }
                    ]
                }
            }
        }

        self.possible_span_labels = [
            {
                "id": "PARTY",
                "color": "#FF0000",
                "description": "A party in the contract",
                "icon": "user",
                "text": "Party",
                "label_type": LabelType.TOKEN_LABEL
            }
        ]

        self.possible_doc_labels = [
            {
                "id": "CONTRACT",
                "color": "#00FF00",
                "description": "A contract document",
                "icon": "file-text",
                "text": "Contract",
                "label_type": LabelType.DOC_TYPE_LABEL
            }
        ]

        self.possible_relationship_labels = []

        self.suggested_label_set = {
            "id": "test-label-set",
            "title": "Test Label Set",
            "description": "A test label set",
            "icon_data": None,
            "icon_name": None,
            "creator": "test@example.com"
        }

    def test_package_job_results_successful(self):
        result = package_job_results_to_oc_generated_corpus_type(
            self.job_results,
            self.possible_span_labels,
            self.possible_doc_labels,
            self.possible_relationship_labels,
            self.suggested_label_set
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(is_dict_instance_of_typed_dict(result, OpenContractsGeneratedCorpusPythonType))

        self.assertIn("annotated_docs", result)
        self.assertIn("doc_labels", result)
        self.assertIn("text_labels", result)
        self.assertIn("label_set", result)

        self.assertEqual(len(result["annotated_docs"]), 1)
        self.assertEqual(len(result["doc_labels"]), 1)
        self.assertEqual(len(result["text_labels"]), 1)
        self.assertEqual(result["label_set"], self.suggested_label_set)

    def test_package_job_results_empty_input(self):
        empty_job_results = {}
        result = package_job_results_to_oc_generated_corpus_type(
            empty_job_results,
            self.possible_span_labels,
            self.possible_doc_labels,
            self.possible_relationship_labels,
            self.suggested_label_set
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(is_dict_instance_of_typed_dict(result, OpenContractsGeneratedCorpusPythonType))
        self.assertEqual(len(result["annotated_docs"]), 0)

    def test_package_job_results_invalid_input(self):
        invalid_job_results = {
            1: {
                "doc_id": 1,
                "task_status": "SUCCESS",
                "task_message": "Document processed successfully",
                "annotations": "Invalid annotations"  # This should be a dict, not a string
            }
        }

        with self.assertRaises(ValueError):
            package_job_results_to_oc_generated_corpus_type(
                invalid_job_results,
                self.possible_span_labels,
                self.possible_doc_labels,
                self.possible_relationship_labels,
                self.suggested_label_set
            )

    def test_package_job_results_multiple_docs(self):
        multi_doc_job_results = {
            1: self.job_results[1],
            2: {
                "doc_id": 2,
                "task_status": "SUCCESS",
                "task_message": "Document processed successfully",
                "annotations": {
                    "doc_labels": ["CONTRACT"],
                    "labelled_text": []
                }
            }
        }

        result = package_job_results_to_oc_generated_corpus_type(
            multi_doc_job_results,
            self.possible_span_labels,
            self.possible_doc_labels,
            self.possible_relationship_labels,
            self.suggested_label_set
        )

        self.assertEqual(len(result["annotated_docs"]), 2)


if __name__ == '__main__':
    unittest.main()