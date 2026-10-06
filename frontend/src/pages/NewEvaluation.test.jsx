import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import NewEvaluation from './NewEvaluation';
import { evaluateStudent, getEvaluationProgress } from '../services/evaluationApi';

vi.mock('../services/evaluationApi', () => ({ evaluateStudent: vi.fn(), getEvaluationProgress: vi.fn() }));

describe('NewEvaluation', () => {
  beforeEach(() => vi.clearAllMocks());
  it('requires all three documents before submission', async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><NewEvaluation /></MemoryRouter>);
    await user.click(screen.getByRole('button', { name: /start evaluation/i }));
    expect(screen.getByRole('alert')).toHaveTextContent('Select a question paper, model answer, and student answer sheet');
  });

  it('polls the same request key and updates stages until the submission finishes', async () => {
    const user = userEvent.setup();
    let finish;
    evaluateStudent.mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
    getEvaluationProgress.mockResolvedValueOnce({ stage: 'reading', status: 'processing', message: 'OCR attempt 1: 2955 characters.', events: [] })
      .mockResolvedValue({ stage: 'analyzing', status: 'processing', message: 'Evaluating answer 1 of 8.', events: [] });
    const { container } = render(<MemoryRouter><NewEvaluation /></MemoryRouter>);
    for (const input of container.querySelectorAll('input[type="file"]')) {
      await user.upload(input, new File(['%PDF'], 'answers.pdf', { type: 'application/pdf' }));
    }
    await user.click(screen.getByRole('button', { name: /start evaluation/i }));
    expect(await screen.findByText(/OCR attempt 1/)).toBeInTheDocument();
    expect(screen.getByText('Reading handwritten answers')).toHaveAttribute('aria-current', 'step');
    await waitFor(() => expect(screen.getByText('Analyzing answers')).toHaveAttribute('aria-current', 'step'), { timeout: 2500 });
    const key = evaluateStudent.mock.calls[0][0].idempotencyKey;
    expect(getEvaluationProgress.mock.calls.every(([requestKey]) => requestKey === key)).toBe(true);
    const signal = getEvaluationProgress.mock.calls[0][1];
    await act(async () => finish({ evaluation_id: 'evaluation_test' }));
    expect(signal.aborted).toBe(true);
  });
});
