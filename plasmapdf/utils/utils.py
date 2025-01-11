import logging
from typing import Any, Dict, List, Union

from pydantic import TypeAdapter, ValidationError

from plasmapdf.models.types import (
    AnnotationLabelPythonType,
    OpenContractsDocAnnotations,
    OpenContractsGeneratedCorpusPythonType,
    OpenContractsLabelSetType,
)

logger = logging.getLogger(__name__)


def is_dict_instance_of_typed_dict(obj: Any, typed_dict_class: Any) -> bool:
    """
    Check if a dictionary matches the structure of a TypedDict class
    """
    # validate with pydantic
    try:

        TypeAdapter(typed_dict_class).validate_python(obj)
        return True

    except ValidationError as exc:
        print(f"ERROR: Invalid schema: {exc}")
        return False


def package_job_results_to_oc_generated_corpus_type(
    job_results: Dict[Union[int, str], OpenContractsDocAnnotations],
    text_labels: List[AnnotationLabelPythonType],
    doc_labels: List[AnnotationLabelPythonType],
    suggested_label_set: OpenContractsLabelSetType,
) -> OpenContractsGeneratedCorpusPythonType:

    print(f"job_results: {job_results}")
    print(f"Suggest label set: {suggested_label_set}")

    oc_corpus_type_dict: OpenContractsGeneratedCorpusPythonType = {
        "annotated_docs": job_results,
        "doc_labels": {label["id"]: label for label in doc_labels},
        "text_labels": {label["id"]: label for label in text_labels},
        "label_set": suggested_label_set,
    }

    logger.info(
        f"package_job_results_to_oc_generated_corpus_type() - oc_corpus_type_dict: {oc_corpus_type_dict}"
    )

    if not is_dict_instance_of_typed_dict(
        oc_corpus_type_dict, OpenContractsGeneratedCorpusPythonType
    ):
        raise ValueError(
            "Job return value does not conform to OpenContractsGeneratedCorpusPythonType"
        )

    logger.info(
        f"package_job_results_to_oc_generated_corpus_type() - OK... return transformed data... {oc_corpus_type_dict}"
    )

    return oc_corpus_type_dict
