import { CircleCheckBig, CircleDashed, CircleX, ClipboardList, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import EmptyState from '../components/common/EmptyState';
import ErrorMessage from '../components/common/ErrorMessage';
import LoadingState from '../components/common/LoadingState';
import EvaluationTable from '../components/results/EvaluationTable';
import { getEvaluations } from '../services/evaluationApi';

const statDefinitions = [
  ['Total Evaluations', ClipboardList, 'total'], ['Completed', CircleCheckBig, 'complete'], ['Partially Evaluated', CircleDashed, 'partially_evaluated'], ['Failed', CircleX, 'failed'],
];

export default function Dashboard() {
  const [state, setState] = useState({ loading: true, error: null, totals: {}, recent: [] });
  const load = async () => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const [all, complete, partial] = await Promise.all([
        getEvaluations({ pageSize: 6 }), getEvaluations({ pageSize: 1, status: 'complete' }), getEvaluations({ pageSize: 1, status: 'partially_evaluated' }),
      ]);
      setState({ loading: false, error: null, recent: all.items || [], totals: { total: all.total, complete: complete.total, partially_evaluated: partial.total, failed: Math.max(0, all.total - complete.total - partial.total) } });
    } catch (error) { setState({ loading: false, error, totals: {}, recent: [] }); }
  };
  useEffect(() => { load(); }, []);
  if (state.loading) return <LoadingState label="Loading overview..." />;
  if (state.error) return <ErrorMessage error={state.error} onRetry={load} />;
  return <div className="page-stack"><section className="page-intro"><div><p className="eyebrow">Overview</p><h2>Assessment activity</h2></div><Link className="primary-button" to="/evaluate"><Plus aria-hidden="true" />New Evaluation</Link></section><section className="dashboard-stats" aria-label="Evaluation statistics">{statDefinitions.map(([label, Icon, key]) => <article className="stat-card" key={key}><Icon aria-hidden="true" /><span>{label}</span><strong>{state.totals[key] ?? 0}</strong></article>)}</section><section className="content-section"><div className="section-heading"><div><p className="eyebrow">Recent activity</p><h2>Recent evaluations</h2></div><Link className="text-link" to="/evaluations">View all</Link></div>{state.recent.length ? <EvaluationTable evaluations={state.recent} /> : <EmptyState detail="Start by submitting an answer sheet for evaluation." action={<Link className="primary-button" to="/evaluate"><Plus />New Evaluation</Link>} />}</section></div>;
}
