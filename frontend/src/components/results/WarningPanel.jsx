import { AlertTriangle } from 'lucide-react';

export default function WarningPanel({ warnings = [] }) {
  if (!warnings.length) return null;
  return <section className="warning-panel"><AlertTriangle aria-hidden="true" /><div><h2>Warnings</h2><ul>{warnings.map((warning, index) => <li key={`${warning}-${index}`}>{warning}</li>)}</ul></div></section>;
}
