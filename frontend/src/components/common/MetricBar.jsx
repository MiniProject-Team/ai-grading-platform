import { formatPercentage, titleCase } from '../../utils/formatters';

export default function MetricBar({ label, value }) {
  const percentage = typeof value === 'number' ? Math.max(0, Math.min(100, value * 100)) : 0;
  return <div className="metric-bar"><div className="metric-label"><span>{titleCase(label)}</span><strong>{typeof value === 'number' ? formatPercentage(percentage) : 'Unavailable'}</strong></div><div className="bar-track"><span className="bar-fill" style={{ width: `${percentage}%` }} /></div></div>;
}
