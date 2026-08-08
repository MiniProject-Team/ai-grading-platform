import { ArrowLeft, History, RotateCcw } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import EmptyState from '../components/common/EmptyState';
import ErrorMessage from '../components/common/ErrorMessage';
import LoadingState from '../components/common/LoadingState';
import EvaluationSummary from '../components/results/EvaluationSummary';
import QuestionResultCard from '../components/results/QuestionResultCard';
import WarningPanel from '../components/results/WarningPanel';
import { getEvaluation } from '../services/evaluationApi';

export default function EvaluationDetails() {
  const { evaluationId } = useParams();
  const [state, setState] = useState({ loading: true, error: null, evaluation: null });
  const load = async () => { setState({ loading: true, error: null, evaluation: null }); try { setState({ loading: false, error: null, evaluation: await getEvaluation(evaluationId) }); } catch (error) { setState({ loading: false, error, evaluation: null }); } };
  useEffect(() => { load(); }, [evaluationId]);
  if (state.loading) return <LoadingState label="Loading stored evaluation..." />;
  if (state.error) return <ErrorMessage error={state.error} onRetry={load} />;
  const evaluation = state.evaluation;
  const studentId = evaluation?.student_information?.student_id;
  const examId = evaluation?.exam_information?.exam_id;
  const failed = evaluation?.status === 'failed';
  return <div className="page-stack"><div className="detail-actions"><Link className="text-link" to="/evaluations"><ArrowLeft />Evaluation History</Link>{studentId && <Link className="secondary-button" to={`/evaluations?studentId=${encodeURIComponent(studentId)}&studentHistory=1`}><History />View Student History</Link>}{examId && <Link className="secondary-button" to={`/evaluations?examId=${encodeURIComponent(examId)}&examHistory=1`}><History />View Exam History</Link>}</div>{failed ? <section className="failed-state"><h2>Evaluation Failed</h2><p>{evaluation.warnings?.[0] || 'The evaluation could not be completed.'}</p><Link className="primary-button" to="/evaluate"><RotateCcw />Try Again</Link></section> : <><EvaluationSummary evaluation={evaluation} />{evaluation.status === 'partially_evaluated' && <section className="partial-notice">Some questions could not be evaluated. Review the warnings and unavailable results below.</section>}<WarningPanel warnings={evaluation.warnings} /><section className="question-results"><div className="section-heading"><div><p className="eyebrow">Question-wise results</p><h2>{evaluation.question_results?.length || 0} question results</h2></div></div>{evaluation.question_results?.length ? evaluation.question_results.map((result) => <QuestionResultCard key={result.question_id} result={result} />) : <EmptyState title="No question results available." />}</section></>}</div>;
}
