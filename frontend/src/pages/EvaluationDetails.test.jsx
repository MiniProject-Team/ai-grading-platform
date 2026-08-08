import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';
import EvaluationDetails from './EvaluationDetails';

vi.mock('../services/evaluationApi', () => ({ getEvaluation: vi.fn() }));
import { getEvaluation } from '../services/evaluationApi';

const partialEvaluation = {
  evaluation_id: 'evaluation_1', status: 'partially_evaluated', student_information: { student_id: 's1', student_name: 'Ada' }, exam_information: { exam_name: 'AI' },
  summary: { awarded_marks: 8, exam_maximum_marks: 10, evaluated_questions: 1, total_questions: 2, unanswered_questions: 1, percentage: 80 },
  warnings: ['Q2 could not be evaluated.'], question_results: [{ question_id: 'Q1', question: 'Define AI.', student_answer: 'A field.', model_answer: 'Artificial intelligence.', evaluation: { status: 'partially_correct', semantic_similarity: .7, concept_coverage: .6, relevance: .8, completeness: .5 }, marks: { awarded: 8, maximum: 10, percentage: 80 }, feedback: { strengths: ['Relevant answer'], missing_concepts: [], weak_areas: [], improvement_suggestions: [], overall_feedback: 'Add detail.' } }],
};

describe('EvaluationDetails', () => {
  it('renders a partial report and question results', async () => {
    getEvaluation.mockResolvedValue(partialEvaluation);
    render(<MemoryRouter initialEntries={['/evaluations/evaluation_1']}><Routes><Route path="/evaluations/:evaluationId" element={<EvaluationDetails />} /></Routes></MemoryRouter>);
    expect(await screen.findByText('Some questions could not be evaluated. Review the warnings and unavailable results below.')).toBeInTheDocument();
    expect(screen.getByText('Q2 could not be evaluated.')).toBeInTheDocument();
    expect(screen.getByText('Define AI.')).toBeInTheDocument();
  });
});
