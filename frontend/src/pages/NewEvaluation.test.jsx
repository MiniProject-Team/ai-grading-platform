import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import NewEvaluation from './NewEvaluation';

describe('NewEvaluation', () => {
  it('requires all three documents before submission', async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><NewEvaluation /></MemoryRouter>);
    await user.click(screen.getByRole('button', { name: /start evaluation/i }));
    expect(screen.getByRole('alert')).toHaveTextContent('Select a question paper, model answer, and student answer sheet');
  });
});
