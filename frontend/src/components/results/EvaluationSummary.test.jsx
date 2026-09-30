import { render, screen } from '@testing-library/react';
import EvaluationSummary from './EvaluationSummary';

it('displays backend totals and OR selections without recomputing the percentage', () => {
  render(<EvaluationSummary evaluation={{ status: 'complete', summary: {
    awarded_marks: 11.6, exam_maximum_marks: 15, percentage: 77.08,
    total_questions: 8, evaluated_questions: 8,
    or_groups: { OR_1: { selected_alternative: 'Q2' }, OR_2: { selected_alternative: 'Q3' } },
  } }} />);
  expect(screen.getByText(/OR_1: Counted Q2/)).toBeInTheDocument();
  expect(screen.getByText(/OR_2: Counted Q3/)).toBeInTheDocument();
  expect(screen.getByText('77.1%')).toBeInTheDocument();
  expect(screen.getByText('11.6')).toBeInTheDocument();
});
