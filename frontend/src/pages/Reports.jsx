import { FileCheck2, Plus } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import EmptyState from '../components/common/EmptyState';
import ErrorMessage from '../components/common/ErrorMessage';
import LoadingState from '../components/common/LoadingState';
import Pagination from '../components/common/Pagination';
import EvaluationTable from '../components/results/EvaluationTable';
import { getEvaluations } from '../services/evaluationApi';

export default function Reports() {
  const [page, setPage] = useState(1);
  const [state, setState] = useState({ loading: true, error: null, data: { items: [], total: 0, page: 1, page_size: 20 } });

  const load = async () => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const data = await getEvaluations({ page, pageSize: 20, status: 'complete' });
      setState({ loading: false, error: null, data });
    } catch (error) {
      setState((current) => ({ ...current, loading: false, error }));
    }
  };

  useEffect(() => { load(); }, [page]);

  const { data } = state;
  return <div className="page-stack">
    <section className="page-intro">
      <div><p className="eyebrow">Completed work</p><h2>Reports</h2></div>
      <Link className="primary-button" to="/evaluate"><Plus aria-hidden="true" />New Evaluation</Link>
    </section>
    <p className="reports-description"><FileCheck2 aria-hidden="true" />Only completed evaluations appear here. Open a record to view its full report.</p>
    {state.loading ? <LoadingState label="Loading completed reports..." /> : state.error ? <ErrorMessage error={state.error} onRetry={load} /> : data.items?.length ? <section className="content-section">
      <EvaluationTable evaluations={data.items} />
      <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
    </section> : <EmptyState title="No completed reports yet." detail="Completed evaluations will be available here." action={<Link className="primary-button" to="/evaluate"><Plus aria-hidden="true" />New Evaluation</Link>} />}
  </div>;
}
