import { ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import EvaluationStatus from '../common/EvaluationStatus';
import { formatDate, formatMarks, formatPercentage } from '../../utils/formatters';

export default function EvaluationTable({ evaluations = [] }) {
  return <div className="table-wrap"><table><thead><tr><th>Evaluation</th><th>Student</th><th>Exam</th><th>Date</th><th>Status</th><th>Marks</th><th>Percentage</th><th><span className="visually-hidden">Open</span></th></tr></thead><tbody>{evaluations.map((item) => { const summary = item.summary || {}; return <tr key={item.evaluation_id}><td><span className="evaluation-id">{item.evaluation_id}</span></td><td>{item.student_information?.student_name || item.student_information?.student_id || 'Anonymous'}</td><td>{item.exam_information?.exam_name || item.exam_information?.exam_id || 'Not recorded'}</td><td>{formatDate(item.created_at)}</td><td><EvaluationStatus status={item.status} /></td><td>{formatMarks(summary.awarded_marks)} / {formatMarks(summary.exam_maximum_marks)}</td><td>{formatPercentage(summary.percentage)}</td><td><Link className="icon-button" aria-label={`Open ${item.evaluation_id}`} to={`/evaluations/${encodeURIComponent(item.evaluation_id)}`}><ChevronRight /></Link></td></tr>; })}</tbody></table></div>;
}
