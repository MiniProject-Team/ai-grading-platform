import { AlertCircle } from 'lucide-react';

export default function ErrorMessage({ error, onRetry }) {
  return <div className="error-message" role="alert"><AlertCircle aria-hidden="true" /><div><strong>Something needs attention</strong><p>{error?.message || 'The request could not be completed.'}</p>{onRetry && <button className="text-button" onClick={onRetry}>Try again</button>}</div></div>;
}
