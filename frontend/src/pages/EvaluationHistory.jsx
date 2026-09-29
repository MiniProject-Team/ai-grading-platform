import { Filter, Plus, RotateCcw } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import EmptyState from '../components/common/EmptyState';
import ErrorMessage from '../components/common/ErrorMessage';
import LoadingState from '../components/common/LoadingState';
import Pagination from '../components/common/Pagination';
import EvaluationTable from '../components/results/EvaluationTable';
import Dashboard from './Dashboard';
import { getEvaluations, getExamEvaluations, getStudentEvaluations } from '../services/evaluationApi';

const defaultFilters = { studentId: '', examId: '', status: '' };

export default function EvaluationHistory() {
  const [searchParams] = useSearchParams();
  const studentHistory = searchParams.get('studentHistory') === '1';
  const examHistory = searchParams.get('examHistory') === '1';
  const searchQuery = (searchParams.get('search') || '').trim().toLocaleLowerCase();
  const initialStudent = searchParams.get('studentId') || '';
  const initialExam = searchParams.get('examId') || '';
  const [draft, setDraft] = useState({ ...defaultFilters, studentId: initialStudent, examId: initialExam });
  const [filters, setFilters] = useState({ ...defaultFilters, studentId: initialStudent, examId: initialExam });
  const [page, setPage] = useState(1);
  const [state, setState] = useState({ loading: true, error: null, data: { items: [], total: 0, page: 1, page_size: 20 } });
  const load = async () => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const queryFilters = { studentId: filters.studentId || undefined, examId: filters.examId || undefined, status: filters.status || undefined };
      if (searchQuery) {
        const firstPage = await getEvaluations({ ...queryFilters, page: 1, pageSize: 100 });
        const pageCount = Math.ceil(firstPage.total / 100);
        const remainingPages = await Promise.all(Array.from({ length: Math.max(0, pageCount - 1) }, (_, index) => getEvaluations({ ...queryFilters, page: index + 2, pageSize: 100 })));
        const allItems = [ ...(firstPage.items || []), ...remainingPages.flatMap((result) => result.items || []) ];
        const matching = allItems.filter((item) => {
          const student = item.student_information || {};
          const exam = item.exam_information || {};
          const searchable = [item.evaluation_id, item.status, student.student_name, student.student_id, student.roll_number, student.subject, exam.exam_name, exam.exam_id, exam.subject]
            .filter(Boolean).join(' ').toLocaleLowerCase();
          return searchable.includes(searchQuery);
        });
        const pageSize = 20;
        setState({ loading: false, error: null, data: { items: matching.slice((page - 1) * pageSize, page * pageSize), total: matching.length, page, page_size: pageSize } });
      } else {
        const data = studentHistory && filters.studentId ? await getStudentEvaluations(filters.studentId, { page, pageSize: 20, examId: filters.examId || undefined }) : examHistory && filters.examId ? await getExamEvaluations(filters.examId, { page, pageSize: 20 }) : await getEvaluations({ ...queryFilters, page, pageSize: 20 });
        setState({ loading: false, error: null, data });
      }
    } catch (error) { setState((current) => ({ ...current, loading: false, error })); }
  };
  useEffect(() => { load(); }, [page, filters.studentId, filters.examId, filters.status, studentHistory, examHistory, searchQuery]);
  const applyFilters = (event) => { event.preventDefault(); setPage(1); setFilters(draft); };
  const reset = () => { setDraft(defaultFilters); setFilters(defaultFilters); setPage(1); };
  const { data } = state;
  const title = searchQuery ? `Search results for “${searchParams.get('search')}”` : studentHistory ? `Student history: ${filters.studentId || 'Unknown student'}` : examHistory ? `Exam history: ${filters.examId || 'Unknown exam'}` : 'Evaluation history';
  const emptyTitle = searchQuery ? 'No matching evaluations.' : studentHistory ? 'No student history yet.' : examHistory ? 'No exam history yet.' : 'No evaluations yet.';
  return <div className="page-stack"><Dashboard /><section className="page-intro"><div><p className="eyebrow">Evaluation records</p><h2>{title}</h2></div><Link className="primary-button" to="/evaluate"><Plus />New Evaluation</Link></section>{searchQuery && <p className="search-hint">Search checks evaluation IDs, student and exam names or IDs, subject, and status.</p>}<form className="filter-bar" onSubmit={applyFilters}><label>Student ID<input value={draft.studentId} onChange={(event) => setDraft((current) => ({ ...current, studentId: event.target.value }))} /></label><label>Exam ID<input value={draft.examId} onChange={(event) => setDraft((current) => ({ ...current, examId: event.target.value }))} /></label>{!studentHistory && !examHistory && <label>Status<select value={draft.status} onChange={(event) => setDraft((current) => ({ ...current, status: event.target.value }))}><option value="">All statuses</option><option value="complete">Complete</option><option value="partially_evaluated">Partially evaluated</option><option value="failed">Failed</option></select></label>}<button className="secondary-button" type="submit"><Filter />Apply</button><button className="icon-text-button" type="button" onClick={reset}><RotateCcw />Reset</button></form>{state.loading ? <LoadingState label="Loading evaluation history..." /> : state.error ? <ErrorMessage error={state.error} onRetry={load} /> : data.items?.length ? <section className="content-section"><EvaluationTable evaluations={data.items} /><Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} /></section> : <EmptyState title={emptyTitle} detail="Adjust filters or start a new evaluation." action={<Link className="primary-button" to="/evaluate"><Plus />New Evaluation</Link>} />}</div>;
}
