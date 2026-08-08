import { AlertTriangle, CheckCircle2, CircleX } from 'lucide-react';
import { titleCase } from '../../utils/formatters';

export default function EvaluationStatus({ status }) {
  const normalized = status || 'unknown';
  const Icon = normalized === 'complete' ? CheckCircle2 : normalized === 'failed' ? CircleX : AlertTriangle;
  return <span className={`status-badge status-${normalized}`}><Icon aria-hidden="true" />{titleCase(normalized)}</span>;
}
