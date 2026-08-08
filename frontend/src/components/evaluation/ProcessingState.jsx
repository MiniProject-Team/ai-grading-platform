const stages = ['Uploading files', 'Reading handwritten answers', 'Analyzing answers', 'Calculating marks', 'Generating feedback', 'Preparing report'];

export default function ProcessingState() {
  return <section className="processing-state" role="status" aria-live="polite"><span className="spinner large" aria-hidden="true" /><div><p className="eyebrow">Evaluation in progress</p><h2>Processing answer sheet...</h2><p>SmartEval is working through the submitted documents. This can take a few minutes.</p><ol>{stages.map((stage, index) => <li key={stage} className={index === 0 ? 'current' : ''}>{stage}</li>)}</ol></div></section>;
}
