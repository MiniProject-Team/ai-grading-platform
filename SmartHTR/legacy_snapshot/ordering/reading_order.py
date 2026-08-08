"""
---------------------------------------------------------
Module    : reading_order.py
Project   : SmartHTR

Description:
    Sort detected text regions into reading order.
---------------------------------------------------------
"""

from __future__ import annotations

from core.entities import Page

from .base_ordering import BaseOrdering


class ReadingOrder(BaseOrdering):
    """
    Sort detections into reading order.
    """

    def order(
        self,
        page: Page,
    ) -> None:
        """
        Sort detections from top-to-bottom and
        left-to-right.
        """

        page.detections.sort(

            key=lambda detection: (

                detection.bbox.top,

                detection.bbox.left,

            )

        )

        page.metadata.add(

            "reading_order",

            {

                "method": "top-bottom-left-right",

                "total_regions": len(
                    page.detections
                ),

            },

        )