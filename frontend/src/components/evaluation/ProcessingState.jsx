const stages = [
  ['uploading', 'Uploading files'], ['reading', 'Reading handwritten answers'],
  ['analyzing', 'Analyzing answers'], ['marks', 'Calculating marks'],
  ['feedback', 'Generating feedback'], ['report', 'Preparing report'],
];

export default function ProcessingState({ progress, progressUnavailable = false }) {
  const stage = progress?.stage || 'uploading';
  const currentIndex = stages.findIndex(([key]) => key === stage);
  const events = progress?.events || [];
  const finished = progress?.status === 'complete';
  return <section className="processing-state" role="status" aria-live="polite"><span className="spinner large" aria-hidden="true" /><div>
    <p className="eyebrow">Evaluation in progress</p>
    <h2>{finished ? 'Evaluation complete' : progress?.status === 'failed' ? 'Evaluation failed' : 'Processing answer sheet...'}</h2>
    <p>{progress?.message || 'Uploading files. Progress will appear as SmartEval processes your documents.'}</p>
    {progressUnavailable && <p className="progress-connection">Live updates are temporarily unavailable. Reconnecting…</p>}
    <ol aria-label="Evaluation stages">{stages.map(([key, label], index) => {
      const completed = finished || (currentIndex >= 0 && index < currentIndex);
      return <li key={key} className={completed ? 'completed' : key === stage ? 'current' : ''} aria-current={key === stage ? 'step' : undefined}>{label}{completed && <span className="stage-complete"> — Done</span>}</li>;
    })}</ol>
    {events.length > 0 && <div className="progress-activity"><h3>Recent activity</h3><ul>{events.slice(-5).map((event, index) => <li key={`${event.timestamp}-${index}`}>{event.message}</li>)}</ul></div>}
  </div></section>;
}
