import { ClipboardList, Percent, Sigma, UserRound } from 'lucide-react';
import { formatMarks, formatPercentage } from '../../utils/formatters';
import EvaluationStatus from '../common/EvaluationStatus';

export default function EvaluationSummary({ evaluation }) {
  const summary = evaluation?.summary || {};
  const maximum = summary.exam_maximum_marks ?? summary.evaluated_maximum_marks;
  return <section className="summary-band"><div className="result-heading"><div><p className="eyebrow">Evaluation result</p><h2>{evaluation?.student_information?.student_name || evaluation?.student_information?.student_id || 'Student evaluation'}</h2></div><EvaluationStatus status={evaluation?.status} /></div><div className="summary-grid">
    <div className="summary-stat"><Sigma aria-hidden="true" /><span>Marks</span><strong>{formatMarks(summary.awarded_marks)} <small>/ {formatMarks(maximum)}</small></strong></div>
    <div className="summary-stat"><Percent aria-hidden="true" /><span>Percentage</span><strong>{formatPercentage(summary.percentage)}</strong></div>
    <div className="summary-stat"><ClipboardList aria-hidden="true" /><span>Evaluated</span><strong>{summary.evaluated_questions ?? 0} <small>/ {summary.total_questions ?? 0}</small></strong></div>
    <div className="summary-stat"><UserRound aria-hidden="true" /><span>Unanswered</span><strong>{summary.unanswered_questions ?? 0}</strong></div>
  </div></section>;
}
