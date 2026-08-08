const sections = [
  ['Strengths', 'strengths'], ['Missing Concepts', 'missing_concepts'], ['Weak Areas', 'weak_areas'], ['Improvement Suggestions', 'improvement_suggestions'],
];

export default function FeedbackSection({ feedback = {} }) {
  return <section className="feedback-section"><h3>Feedback</h3><div className="feedback-grid">{sections.map(([label, key]) => feedback[key]?.length ? <div key={key}><h4>{label}</h4><ul>{feedback[key].map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul></div> : null)}</div>{feedback.overall_feedback && <p className="overall-feedback">{feedback.overall_feedback}</p>}</section>;
}
