import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { formatMarks, formatPercentage, titleCase } from '../../utils/formatters';
import MetricBar from '../common/MetricBar';
import FeedbackSection from './FeedbackSection';

export default function QuestionResultCard({ result }) {
  const [open, setOpen] = useState(false);
  const marks = result?.marks || {};
  const evaluation = result?.evaluation || {};
  return <article className="question-card"><div className="question-card-header"><div><p className="eyebrow">{result?.question_id || 'Question'}</p><h3>{result?.question || 'Question text unavailable'}</h3></div><div className="question-score"><strong>{formatMarks(marks.awarded)} / {formatMarks(marks.maximum ?? result?.max_marks)}</strong><span>{formatPercentage(marks.percentage)}</span></div></div><div className="question-meta"><div className="question-badges"><span className={`result-status result-${evaluation.status || 'unknown'}`}>{titleCase(evaluation.status || 'unavailable')}</span>{result?.alternative_group && <span className="alternative-group">{result.alternative_group}</span>}</div><button className="icon-text-button" aria-expanded={open} onClick={() => setOpen(!open)}>{open ? <ChevronUp /> : <ChevronDown />}{open ? 'Hide details' : 'View details'}</button></div>
    {open && <div className="question-details"><div className="answer-grid"><div><h4>Student Answer</h4><p>{result?.student_answer || 'No answer provided.'}</p></div><div><h4>Model Answer</h4><p>{result?.model_answer || 'Unavailable.'}</p></div></div><div className="metrics-grid"><MetricBar label="semantic similarity" value={evaluation.semantic_similarity} /><MetricBar label="concept coverage" value={evaluation.concept_coverage} /><MetricBar label="relevance" value={evaluation.relevance} /><MetricBar label="completeness" value={evaluation.completeness} /></div><FeedbackSection feedback={result?.feedback} /></div>}
  </article>;
}
