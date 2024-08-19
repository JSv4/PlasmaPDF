import logging
from typing import TypedDict, Union, cast

import pydantic

from plasmapdf.models.types import (
    OpenContractsDocAnalysisResult,
    OpenContractsGeneratedCorpusPythonType, AnnotationLabelPythonType, OpenContractsLabelSetType,
)

logger = logging.getLogger(__name__)


def is_dict_instance_of_typed_dict(instance: dict, typed_dict: type[TypedDict]):

    # validate with pydantic
    try:
        cast(
            typed_dict,
            pydantic.create_model_from_typeddict(typed_dict)(**instance).dict(),
        )
        return True

    except pydantic.ValidationError as exc:
        logger.info(f"ERROR: Invalid schema error {exc} for {instance}")
        return False


def package_job_results_to_oc_generated_corpus_type(
    job_results: dict[Union[int, str], OpenContractsDocAnalysisResult],
    possible_span_labels: list[AnnotationLabelPythonType],
    possible_doc_labels: list[AnnotationLabelPythonType],
    possible_relationship_labels: list[AnnotationLabelPythonType],
    suggested_label_set: OpenContractsLabelSetType
) -> OpenContractsGeneratedCorpusPythonType:

    oc_corpus_type_dict: OpenContractsGeneratedCorpusPythonType = {
        "annotated_docs": {
            result["doc_id"]: result["annotations"]
            for result in list(job_results.values())
        },
        "doc_labels": {
            label["id"]: label for label in possible_doc_labels
        },
        "text_labels": {
            label["id"]: label for label in possible_span_labels
        },
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
