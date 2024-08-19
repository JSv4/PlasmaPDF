#  Copyright (C) 2022  John Scrudato / Gordium Knot Inc. d/b/a OpenSource.Legal
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import logging
import uuid

import pandas as pd

from plasmapdf.models.types import (
    OpenContractsAnnotationPythonType,
    OpenContractsSinglePageAnnotationType,
    PageAwareTextSpan,
    PawlsPagePythonType,
    SpanAnnotation,
    TextSpan,
)

logger = logging.getLogger(__name__)


def __consolidate_common_equivalent_chars(string):

    # OCR sometimes uses characters similar to what we're looking for in place of actual char.
    # Here we do some quick, naive cleanup of this by replacing some more exotic chars that look
    # like common chars with their common equivalents.

    # Things that commonly look like apostrophes
    for i in "’'´":
        string = string.replace(i, "'")

    # Things that commonly look like periods
    for i in "⋅":
        string = string.replace(i, ".")

    return string


class PdfDataLayer:
    def __init__(
        self,
        pawls_tokens,
        page_dataframe,
        lines_dataframe,
        tokens_dataframe,
        doc_text,
        doc_tokens,
        page_tokens,
        human_friendly_full_text,
    ):
        self.pawls_tokens = pawls_tokens
        self.page_dataframe = page_dataframe
        self.lines_dataframe = lines_dataframe
        self.tokens_dataframe = tokens_dataframe
        self.doc_text = doc_text
        self.doc_tokens = doc_tokens
        self.page_tokens = page_tokens
        self.human_friendly_full_text = human_friendly_full_text
        self.log = ""
        self.pawls_annotations = {}
        self.span_annotations: dict[str, any] = {}

    def get_raw_text_from_span(self, span: TextSpan) -> str:
        return self.doc_text[span["start"] : span["end"]]

    def convert_doc_span_to_opencontract_annotation_json(
        self,
        span: TextSpan,
        padding: float = 0.1,
        max_bbox_vertical_margin: float = 1,
        max_bbox_horizontal_margin: float = 5,
    ) -> dict[int, OpenContractsSinglePageAnnotationType]:

        """
        Given the start and end index of a string in the document, return the PAWLS tokens for the annotation, split
        across pages. For a given page, the annotation will look like:
            {
                "bounds": {
                    "top": top,
                    "bottom": bottom,
                    "left": left,
                    "right": right
                },
                "rawText": page_text,
                "tokensJsons": page_tokens
            }
        """

        span_start = span["start"]
        span_end = span["end"]

        # logger.info(f"Get tokens in char range {span_start} - {span_end}")
        tokens = self.tokens_dataframe[
            (
                (self.tokens_dataframe["Char_Start"] >= span_start)
                & (self.tokens_dataframe["Char_Start"] <= span_end)
            )
            | (
                (self.tokens_dataframe["Char_End"] >= span_start)
                & (self.tokens_dataframe["Char_End"] <= span_end)
            )
        ]

        return_annotations = {}
        page_tokens = []
        page_text = ""

        last_page = -1

        bbox_top = -1
        bbox_bottom = -1
        bbox_left = -1
        bbox_right = -1

        for token in tokens.iterrows():

            token_page = token[1]["Page"]

            # logger.info(f"Handle token page: {token_page}")

            if last_page == -1:
                last_page = token_page

            token_page_id = token[1]["Token_Id"]
            token_obj = self.page_tokens[token_page][token_page_id]
            token_height = token_obj["height"]
            token_width = token_obj["width"]

            ###########################################################################
            #                                                                         #
            # Check / Update Bounding Box                                             #
            #                                                                         #
            # Top Left Corner is 0,0. Y increases as you move down page.              #
            # Update bounding box to include token in it                              #
            ###########################################################################
            token_top = token_obj["y"]
            if bbox_top == -1:
                bbox_top = token_top
            elif token_top < bbox_top:
                bbox_top = token_top

            token_bottom = token_top + token_height
            if bbox_bottom == -1:
                bbox_bottom = token_bottom
            elif token_bottom > bbox_bottom:
                bbox_bottom = token_bottom

            token_left = token_obj["x"]
            if bbox_left == -1:
                bbox_left = token_left
            elif token_left < bbox_left:
                bbox_left = token_left

            token_right = token_left + token_width
            if bbox_right == -1:
                bbox_right = token_right
            elif token_right > bbox_right:
                bbox_right = token_right

            # If we changed pages... reset bounds and add bounding box to tracker
            if token_page != last_page:

                bbox_height = bbox_bottom - bbox_top
                logger.info(f"Height: {bbox_height}")
                bbox_width = bbox_right - bbox_left
                logger.info(f"Width: {bbox_width}")

                return_annotations[last_page] = {
                    "bounds": {
                        "top": bbox_top - (padding * bbox_height),
                        "bottom": bbox_bottom + (padding * bbox_height),
                        "left": bbox_left - (padding * bbox_width),
                        "right": bbox_right + (padding * bbox_width),
                    },
                    "rawText": page_text,
                    "tokensJsons": page_tokens,
                }

                # Reset tracking vars
                last_page = token_page
                page_text = token_obj["text"]
                page_tokens = [{"pageIndex": token_page, "tokenIndex": token_page_id}]

                bbox_top = -1
                bbox_bottom = -1
                bbox_left = -1
                bbox_right = -1

            else:

                page_text += (
                    token_obj["text"] if page_text == "" else (" " + token_obj["text"])
                )
                page_tokens.append(
                    {"pageIndex": token_page, "tokenIndex": token_page_id}
                )

        bbox_height = bbox_bottom - bbox_top
        logger.info(f"Height: {bbox_height}")
        bbox_width = bbox_right - bbox_left
        logger.info(f"Width: {bbox_width}")

        bbox_vertical_margin = padding * bbox_height / 2
        if bbox_vertical_margin > max_bbox_vertical_margin:
            bbox_vertical_margin = max_bbox_vertical_margin

        bbox_horizontal_margin = padding * bbox_width / 2
        if bbox_horizontal_margin > max_bbox_horizontal_margin:
            bbox_horizontal_margin = max_bbox_horizontal_margin

        return_annotations[last_page] = {
            "bounds": {
                "top": bbox_top - bbox_vertical_margin,
                "bottom": bbox_bottom + bbox_vertical_margin,
                "left": bbox_left - bbox_horizontal_margin,
                "right": bbox_right + bbox_horizontal_margin,
            },
            "rawText": page_text,
            "tokensJsons": page_tokens,
        }

        return return_annotations

    # TODO - This doesn't appear to work properly and is ONLY used to determine the
    # TODO - first page of a given annotation? Get rid of this if possible.
    # TODO - Just extra code to maintain. It's useless.
    def split_span_on_pages(self, span: TextSpan) -> list[PageAwareTextSpan]:

        span_start = span["start"]
        print(f"Span start: {span_start}")
        span_end = span["end"]
        print(f"Span end: {span_end}")

        print(f"Split lines for char range {span_start} - {span_end}")

        pages = self.page_dataframe[
            (
                (span_start >= self.page_dataframe["Start"])
                & (span_start <= self.page_dataframe["End"])
            )
            | (
                (span_start < self.page_dataframe["Start"])
                & (span_end > self.page_dataframe["End"])
            )
            | (
                (span_end >= self.page_dataframe["Start"])
                & (span_end <= self.page_dataframe["End"])
            )
        ]

        print(f"Pages: {pages}")

        # logger.info(f"Resulting pages: {pages}")

        page_split_spans: list[PageAwareTextSpan] = []

        for page in pages.iterrows():

            print(f"Look at page # {page[0]} with start "
                        f"{page[1]['Start']} and end "
                        f"{page[1]['End']}")

            # Calculate the start of target span... if the span starts
            # before this page, use the page start index. Otherwise, use the
            # page start index.
            if span_start <= page[1]["Start"]:
                span_page_start = page[1]["Start"]
            else:
                span_page_start = span_start

            # Calculate the end of this page's span... if the span ends after this
            # page, use the page end index. Otherwise, if span ends on this page,
            # use the span's end index
            if span_end > page[1]["End"]:
                span_page_end = page[1]["End"]
            else:
                span_page_end = span_end

            page_split_spans.append(
                {
                    "original_span_id": span["id"],
                    "page": page[0],
                    "start": span_page_start,
                    "end": span_page_end,
                    "text": self.human_friendly_full_text[
                        span_page_start:span_page_end
                    ],
                }
            )

        return page_split_spans

    def create_opencontract_annotation_from_span(
        self,
        span_annotation: SpanAnnotation,
    ) -> OpenContractsAnnotationPythonType:

        span = span_annotation["span"]
        annotation_label = span_annotation["annotation_label"]

        id = uuid.uuid4().__str__()
        annotation_json = self.convert_doc_span_to_opencontract_annotation_json(span)
        raw_text = self.get_raw_text_from_span(span)
        page = self.split_span_on_pages(span)[0]["page"]  # TODO - this is not working

        return {
            "id": id,
            "annotationLabel": annotation_label,
            "rawText": raw_text,
            "page": page,
            "annotation_json": annotation_json,
        }


def makePdfTranslationLayerFromPawlsTokens(
    pawls_tokens: list[PawlsPagePythonType],
) -> PdfDataLayer:

    page_tokens = {}
    doc_tokens = []
    tokens = []
    pages = []
    lines: list[tuple[int, int, int, int]] = []
    doc_text = ""
    human_friendly_text = ""
    line_start_char = 0

    # We want the last token height to carry over from previous pages, so we have a token
    # height that is useful to compare to if the page starts with whitespace (token height of 0)
    last_token_height = -1

    for page_num, page in enumerate(pawls_tokens):

        # logger.info(f"Looking at page_num {page_num}:\n\n{page}")

        # We DO want to reset y pos on every page, which will be set to y of first token.
        last_y = -1

        line_text = ""
        page_tokens[page_num] = []

        for page_token_index, token in enumerate(page["tokens"]):

            token_text = __consolidate_common_equivalent_chars(token["text"])
            page_tokens[page_num].append(token)
            doc_tokens.append(token)

            new_y = round(token["y"], 0)
            new_token_height = round(token["height"], 0)

            if last_y == -1:
                last_y = round(token["y"], 0)

            if last_token_height == -1:

                # Not really sure how to handle situations where the token height is 0 at the beginning... just
                # try 1 pixel, I guess?
                last_token_height = new_token_height if new_token_height > 0 else 1

            # Tesseract line positions seem a bit erratic, honestly. Figuring out when a token is on the same line is
            # not as easy as checking if y positions are the same as they are often off by a couple pixels. This is
            # dependent on document, font size, OCR quality, and more... Decent heuristic I came up with was to look
            # at two consecutive tokens, take the max token height and then see if the y difference was more than some
            # percentage of the larger of the two token heights (to account for things like periods or dashes or
            # whatever next to a word). Seems to work pretty well, though I am *SURE* it will fail in some cases. Easy
            # enough fix there... just don't give a cr@p about line height and newlines and always use a space. That's
            # actually probably fine for ML purposes.
            # logger.info(f"Token: {token['text']} (len {len(token['text'])})")
            # logger.info(f"Line y difference: {abs(new_y - last_y)}")
            # logger.info(f"Compared to averaged token height: {0.5 * max(new_token_height, last_token_height)}")

            if abs(new_y - last_y) > (0.5 * max(new_token_height, last_token_height)):

                human_friendly_text += (
                    ("\n" + token_text) if len(human_friendly_text) > 0 else token_text
                )

                lines.append(
                    (
                        page_num,
                        len(lines),
                        line_start_char,
                        len(line_text) + line_start_char,
                    )
                )

                line_start_char = len(doc_text) + 1  # Accounting for newline
                line_text = token_text

            else:
                line_text += " " if len(line_text) > 0 else ""
                line_text += token_text

                human_friendly_text += (
                    (" " + token_text) if len(human_friendly_text) > 0 else token_text
                )

            start_length = len(doc_text)
            doc_text += " " if len(doc_text) > 0 else ""
            doc_text += token_text
            end_length = len(doc_text)

            tokens.append(
                [page_num, len(page_tokens[page_num]) - 1, start_length + 1, end_length]
            )

            last_y = new_y

            # We want to compare line heights of non-whitespace chars. If the current token
            # is a whitespace char, its height will be 0, so just leave the last_token_height in place.
            if new_token_height > 0:
                last_token_height = new_token_height

        pages.append(
            [
                page_num,
                (0 if page_num == 0 else pages[page_num - 1][2]),
                len(doc_text),
            ]
        )

        # logger.info(f"Pages: {pages}")

    page_dim_df = pd.DataFrame(pages, columns=["Page", "Start", "End"], dtype=object)
    line_dim_df = pd.DataFrame(
        lines, columns=["Page", "Line", "Char_Start", "Char_End"], dtype=object
    )
    token_dim_df = pd.DataFrame(
        tokens, columns=["Page", "Token_Id", "Char_Start", "Char_End"], dtype=object
    )

    # logger.info(f"page_text: {doc_text}")

    return PdfDataLayer(
        pawls_tokens=pawls_tokens,
        page_dataframe=page_dim_df,
        lines_dataframe=line_dim_df,
        tokens_dataframe=token_dim_df,
        doc_text=doc_text,
        doc_tokens=doc_tokens,
        page_tokens=page_tokens,
        human_friendly_full_text=human_friendly_text,
    )
