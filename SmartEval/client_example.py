"""Minimal client for a locally running SmartEval API."""

from pathlib import Path

import httpx


def evaluate(question_paper: Path, model_answer: Path, student_sheet: Path) -> dict:
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=600) as client:
        with question_paper.open("rb") as question_file, model_answer.open("rb") as model_file, student_sheet.open("rb") as student_file:
            response = client.post(
                "/api/v1/evaluate",
                files={
                    "question_paper": (question_paper.name, question_file, "application/pdf"),
                    "model_answer": (model_answer.name, model_file, "application/pdf"),
                    "student_answer_sheet": (student_sheet.name, student_file, "application/pdf"),
                },
            )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    result = evaluate(Path("inputs/question_paper.pdf"), Path("inputs/model_answer.pdf"), Path("inputs/student_answer_sheet.pdf"))
    print(result["evaluation_id"], result["status"])
