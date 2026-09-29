import { ArrowUpRight, CircleHelp, FileCheck2, Server, Upload } from 'lucide-react';
import { Link } from 'react-router-dom';
import { API_BASE_URL, MAX_UPLOAD_SIZE_MB } from '../config';

const helpTopics = [
  { icon: Upload, title: 'Prepare your files', detail: `Upload a question paper, model answer, and student answer sheet. PDF, PNG, JPG, and JPEG files up to ${MAX_UPLOAD_SIZE_MB} MB are accepted.` },
  { icon: FileCheck2, title: 'Review an evaluation', detail: 'Open Evaluation History to find a report. Select a row to review marks, question results, and feedback.' },
  { icon: Server, title: 'Backend connection', detail: 'If uploads or history fail, check that the SmartEval backend is running and its database connection is available.' },
];

export default function HelpSupport() {
  return <div className="page-stack">
    <section className="page-intro"><div><p className="eyebrow">Help center</p><h2>Using SmartEval</h2></div><a className="secondary-button" href={`${API_BASE_URL}/docs`} target="_blank" rel="noreferrer">API documentation <ArrowUpRight aria-hidden="true" /></a></section>
    <section className="content-section help-intro"><CircleHelp aria-hidden="true" /><div><h2>How can we help?</h2><p>Find quick guidance for submitting and reviewing answer sheet evaluations.</p></div></section>
    <section className="help-grid" aria-label="Help topics">{helpTopics.map(({ icon: Icon, title, detail }) => <article className="help-card" key={title}><Icon aria-hidden="true" /><h3>{title}</h3><p>{detail}</p></article>)}</section>
    <section className="content-section help-next"><h2>Ready to get started?</h2><p>Submit a new evaluation or return to your Home overview.</p><div><Link className="primary-button" to="/evaluate">New Evaluation</Link><Link className="secondary-button" to="/">Go to Home</Link></div></section>
  </div>;
}
