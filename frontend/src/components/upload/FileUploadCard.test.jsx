import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import FileUploadCard from './FileUploadCard';

describe('FileUploadCard', () => {
  it('rejects an unsupported file before submission', () => {
    render(<FileUploadCard id="question" label="Question Paper" helper="Upload" file={null} onChange={() => {}} />);
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [new File(['text'], 'notes.txt', { type: 'text/plain' })] } });
    expect(screen.getByRole('alert')).toHaveTextContent('Choose a PDF, PNG, JPG, or JPEG');
  });

  it('shows a selected valid file and allows removal', () => {
    const onChange = vi.fn();
    const file = new File(['pdf'], 'questions.pdf', { type: 'application/pdf' });
    const { rerender } = render(<FileUploadCard id="question" label="Question Paper" helper="Upload" file={null} onChange={onChange} />);
    fireEvent.change(document.querySelector('input[type="file"]'), { target: { files: [file] } });
    expect(onChange).toHaveBeenCalledWith(file);
    rerender(<FileUploadCard id="question" label="Question Paper" helper="Upload" file={file} onChange={onChange} />);
    expect(screen.getByText('questions.pdf')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Remove Question Paper' }));
    expect(onChange).toHaveBeenLastCalledWith(null);
  });
});
