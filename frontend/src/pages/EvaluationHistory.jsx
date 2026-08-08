import { Filter, Plus, RotateCcw } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import EmptyState from '../components/common/EmptyState';
import ErrorMessage from '../components/common/ErrorMessage';
import LoadingState from '../components/common/LoadingState';
import Pagination from '../components/common/Pagination';
import EvaluationTable from '../components/results/EvaluationTable';
import { getEvaluations, getExamEvaluations, getStudentEvaluations } from '../services/evaluationApi';

const defaultFilters = { studentId: '', examId: '', status: '' };

export default function EvaluationHistory() {
  const [searchParams] = useSearchParams();
  const studentHistory = searchParams.get('studentHistory') === '1';
  const examHistory = searchParams.get('examHistory') === '1';
  const initialStudent = searchParams.get('studentId') || '';
  const initialExam = searchParams.get('examId') || '';
  const [draft, setDraft] = useState({ ...defaultFilters, studentId: initialStudent, examId: initialExam });
  const [filters, setFilters] = useState({ ...defaultFilters, studentId: initialStudent, examId: initialExam });
  const [page, setPage] = useState(1);
  const [state, setState] = useState({ loading: true, error: null, data: { items: [], total: 0, page: 1, page_size: 20 } });
  const load = async () => { setState((current) => ({ ...current, loading: true, error: null })); try { const data = studentHistory && filters.studentId ? await getStudentEvaluations(filters.studentId, { page, pageSize: 20, examId: filters.examId || undefined }) : examHistory && filters.examId ? await getExamEvaluations(filters.examId, { page, pageSize: 20 }) : await getEvaluations({ page, pageSize: 20, studentId: filters.studentId || undefined, examId: filters.examId || undefined, status: filters.status || undefined }); setState({ loading: false, error: null, data }); } catch (error) { setState((current) => ({ ...current, loading: false, error })); } };
  useEffect(() => { load(); }, [page, filters.studentId, filters.examId, filters.status, studentHistory, examHistory]);
  const applyFilters = (event) => { event.preventDefault(); setPage(1); setFilters(draft); };
  const reset = () => { setDraft(defaultFilters); setFilters(defaultFilters); setPage(1); };
  const { data } = state;
  const title = studentHistory ? `Student history: ${filters.studentId || 'Unknown student'}` : examHistory ? `Exam history: ${filters.examId || 'Unknown exam'}` : 'Evaluation history';
  const emptyTitle = studentHistory ? 'No student history yet.' : examHistory ? 'No exam history yet.' : 'No evaluations yet.';
  return <div className="page-stack"><section className="page-intro"><div><p className="eyebrow">Stored reports</p><h2>{title}</h2></div><Link className="primary-button" to="/evaluate"><Plus />New Evaluation</Link></section><form className="filter-bar" onSubmit={applyFilters}><label>Student ID<input value={draft.studentId} onChange={(event) => setDraft((current) => ({ ...current, studentId: event.target.value }))} /></label><label>Exam ID<input value={draft.examId} onChange={(event) => setDraft((current) => ({ ...current, examId: event.target.value }))} /></label>{!studentHistory && !examHistory && <label>Status<select value={draft.status} onChange={(event) => setDraft((current) => ({ ...current, status: event.target.value }))}><option value="">All statuses</option><option value="complete">Complete</option><option value="partially_evaluated">Partially evaluated</option><option value="failed">Failed</option></select></label>}<button className="secondary-button" type="submit"><Filter />Apply</button><button className="icon-text-button" type="button" onClick={reset}><RotateCcw />Reset</button></form>{state.loading ? <LoadingState label="Loading evaluation history..." /> : state.error ? <ErrorMessage error={state.error} onRetry={load} /> : data.items?.length ? <section className="content-section"><EvaluationTable evaluations={data.items} /><Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} /></section> : <EmptyState title={emptyTitle} detail="Adjust filters or start a new evaluation." action={<Link className="primary-button" to="/evaluate"><Plus />New Evaluation</Link>} />}</div>;
}
