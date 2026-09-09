from __future__ import annotations

from .models import ParsedPaper


class AnswerGenerator:
    """Safe answer-sheet scaffold. A subject LLM can replace `draft` later."""
    def generate(self, paper: ParsedPaper, depth: str = "exam_ready") -> str:
        lines = ["MODEL ANSWER SHEET", "", f"Subject: {paper.exam.subject or 'Unknown'}"]
        for section in paper.sections:
            if section.section_name: lines.extend(["", section.section_name.upper()])
            for question in section.questions:
                label = f"Q{question.question_number}" + (f"({question.sub_question})" if question.sub_question else "")
                lines.extend(["", f"{label}. {question.question_text}", "Answer:", self.draft(question.question_text, question.marks, question.question_type, depth)])
        return "\n".join(lines)

    @staticmethod
    def draft(question: str, marks: int | None, question_type: str, depth: str) -> str:
        if question_type == "comparison": return "Use a point-by-point comparison table covering definition, key differences, and an example."
        if question_type == "numerical": return "State the formula, substitute the given values, show each calculation, and clearly state the final result with units."
        if question_type == "programming": return "Explain the approach, provide correct code, and include a representative input/output example."
        scope = "a concise definition and key point" if (marks or 0) <= 2 else "an introduction, structured explanation, relevant example, and conclusion"
        return f"Prepare {scope}. Verify the subject-specific content before publication."
