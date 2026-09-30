"""Read saved OCR text without invoking OCR or evaluation.

Run from SmartEval with PYTHONPATH=. and pass an optional input path.
Positions are zero-based Unicode character offsets (end exclusive).
"""
from collections import defaultdict
from pathlib import Path
import sys

from domain.value_objects.question_id import QuestionId
from parsers.student_answer_parser import HEADING_PATTERN, StudentAnswerParser


def diagnose(path):
    text = path.read_text(encoding='utf-8')
    expected = [QuestionId(n, p) for n in range(1, 5) for p in ('a', 'b')]
    parser = StudentAnswerParser()
    occurrences = defaultdict(list)
    accepted = []
    offset = 0
    count = 0
    for source_line in text.splitlines(keepends=True):
        line = source_line.rstrip('\r\n')
        match = HEADING_PATTERN.match(line)
        candidate = parser._candidate_id(match) if match else None
        if candidate is not None:
            count += 1
            start = offset + len(line) - len(line.lstrip())
            end = offset + match.start('body')
            raw = text[start:end].rstrip()
            end = start + len(raw)
            is_accepted = candidate in expected or (
                bool(match.group('prefix')) and candidate.subpart is None
                and any(q.number == candidate.number for q in expected)
            )
            print(f'CANDIDATE {count}\nraw={raw!r}\nnormalized={candidate}\ncanonical={candidate}\n'
                  f'position=[{start}, {end})\nexpected={candidate in expected}\n'
                  f'context={text[max(0,start-80):min(len(text),end+80)]!r}\n')
            occurrences[str(candidate)].append((start,end,raw))
            if is_accepted:
                accepted.append((start,end,str(candidate)))
        offset += len(source_line)
    print('OCCURRENCES FOR EXPECTED IDS')
    for identifier in expected:
        print(f'{identifier}: {occurrences[str(identifier)]}')
    duplicates = {str(q): occurrences[str(q)] for q in expected if len(occurrences[str(q)]) > 1}
    print('RAW CHARACTERS:',len(text))
    print('ALL REGEX CANDIDATES:',count)
    print('RAW MARKER COUNT (accepted headings):',len(accepted))
    print('DEDUPLICATED MARKER COUNT (diagnostic span/ID set only):',len(set(accepted)))
    print('UNIQUE QUESTION IDS:',list(dict.fromkeys(c[2] for c in accepted)))
    print('DUPLICATES:',duplicates or 'none')
    try:
        answers=parser.parse(text,expected)
        print('PARSED ANSWER COUNT:',len(answers))
        print('PARSED IDS:',[str(a.question_id) for a in answers])
    except ValueError as error:
        print('PARSER ERROR:',error)


if __name__ == '__main__':
    diagnose(Path(sys.argv[1]) if len(sys.argv)>1 else Path('outputs/debug/latest_student_parser_input.txt'))
