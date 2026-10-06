import { render, screen } from '@testing-library/react';
import ProcessingState from './ProcessingState';

describe('ProcessingState', () => {
  it('uses the actual backend stage and OCR activity', () => {
    const { rerender } = render(<ProcessingState />);
    expect(screen.getByText('Uploading files')).toHaveAttribute('aria-current', 'step');
    rerender(<ProcessingState progress={{ stage: 'reading', status: 'processing', message: 'OCR reading attempt 2: 2,955 characters extracted.', events: [] }} />);
    expect(screen.getByText('Reading handwritten answers')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText(/Uploading files/)).toHaveClass('completed');
    expect(screen.getByText(/OCR reading attempt 2/)).toBeInTheDocument();
    expect(screen.getByText('Calculating marks')).not.toHaveClass('completed');
  });

  it('retains the last known stage while reconnecting', () => {
    render(<ProcessingState progress={{ stage: 'analyzing', message: 'Evaluating answer 3 of 8.', events: [] }} progressUnavailable />);
    expect(screen.getByText('Analyzing answers')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText(/Reconnecting/)).toBeInTheDocument();
  });
});
