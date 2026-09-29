import { ArrowDown, ArrowRight, BookOpenCheck, FileCheck2, FileText, ScanText, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

const workflow = [
  { icon: FileText, number: '01', title: 'Add the question paper', detail: 'SmartEval identifies the questions and available marks from the teacher paper.' },
  { icon: BookOpenCheck, number: '02', title: 'Add the model answers', detail: 'Use the expected answers as the reference for evaluating student responses.' },
  { icon: ScanText, number: '03', title: 'Upload student work', detail: 'OCR reads the handwritten sheet and prepares the answers for evaluation.' },
  { icon: FileCheck2, number: '04', title: 'Review the report', detail: 'See question-level results, marks, feedback, and completion status in one place.' },
];

export default function Home() {
  return <main className="landing-page">
    <section className="landing-hero">
      <div className="landing-hero-copy">
        <span className="landing-kicker"><Sparkles aria-hidden="true" />AI-assisted answer evaluation</span>
        <h2>From handwritten pages to clear evaluation reports.</h2>
        <p>SmartEval brings question papers, model answers, and student answer sheets into one teacher-friendly workflow. Review organized results and feedback without losing sight of the work behind each mark.</p>
        <a className="landing-scroll-link" href="#how-it-works">See how it works <ArrowDown aria-hidden="true" /></a>
      </div>
      <div className="landing-visual" aria-label="Illustration of the SmartEval evaluation workflow" role="img">
        <div className="landing-orbit orbit-one" /><div className="landing-orbit orbit-two" />
        <div className="landing-paper paper-question"><FileText aria-hidden="true" /><span>Question paper</span><i /><i /><i /></div>
        <div className="landing-paper paper-answer"><BookOpenCheck aria-hidden="true" /><span>Model answer</span><i /><i /><i /></div>
        <div className="landing-result"><div className="landing-result-top"><span className="result-check"><FileCheck2 aria-hidden="true" /></span><div><strong>Evaluation report</strong><small>Ready for review</small></div><b>Complete</b></div><div className="landing-result-score"><div><small>Question results</small><strong>Clear and organized</strong></div><div className="landing-score-mark">✓</div></div><div className="landing-result-bars"><i /><i /><i /></div></div>
      </div>
    </section>

    <section className="landing-intro" id="how-it-works">
      <p className="eyebrow">Built for the teacher workflow</p>
      <h2>Spend less time organizing papers. Keep every result easy to review.</h2>
      <p>SmartEval combines handwriting recognition with structured answer evaluation. It keeps student responses, marks, and feedback together in a report that teachers can inspect.</p>
    </section>

    <section className="landing-photo-row" aria-label="Study and assessment photos">
      <figure className="landing-photo-card">
        <img src="https://images.unsplash.com/photo-1769794370964-78412732f1cd?auto=format&fit=crop&w=1400&q=82" alt="Study papers, pens, and a highlighter arranged on a desk" loading="lazy" />
        <figcaption><span>Thoughtful review starts with clear student work.</span><a href="https://unsplash.com/photos/a-desk-with-papers-pens-and-a-highlighter-3Hcz2zvPqBI" target="_blank" rel="noreferrer">Photo by Yen Vu on Unsplash</a></figcaption>
      </figure>
      <figure className="landing-photo-card">
        <img src="https://images.unsplash.com/photo-1758685848895-e724272475d2?auto=format&fit=crop&w=1400&q=82" alt="Student studying with a laptop at a desk" loading="lazy" />
        <figcaption><span>Keep learning and evaluation connected.</span><a href="https://unsplash.com/photos/student-studying-at-a-desk-with-a-chalkboard-otASzgFlJ_c" target="_blank" rel="noreferrer">Photo by Vitaly Gariev on Unsplash</a></figcaption>
      </figure>
    </section>

    <section className="landing-workflow" aria-label="How SmartEval works">
      {workflow.map(({ icon: Icon, number, title, detail }) => <article className="workflow-card" key={number}><span className="workflow-number">{number}</span><span className="workflow-icon"><Icon aria-hidden="true" /></span><h3>{title}</h3><p>{detail}</p></article>)}
    </section>

    <section className="landing-feature-band">
      <div className="feature-mark"><ScanText aria-hidden="true" /></div>
      <div><p className="eyebrow">Handwriting to report</p><h2>One connected process, from OCR to teacher review.</h2><p>Handwritten text is extracted, matched to the paper's questions, evaluated against the model answers, and presented with marks and feedback.</p></div>
    </section>

    <section className="landing-cta">
      <span className="landing-kicker"><Sparkles aria-hidden="true" />Your next evaluation starts here</span>
      <h2>Ready to review student work with more clarity?</h2>
      <p>Bring the question paper, model answer, and student answer sheet. SmartEval will organize the evaluation for you to review.</p>
      <Link className="primary-button landing-start-button" to="/evaluate">Start Evaluation <ArrowRight aria-hidden="true" /></Link>
    </section>
  </main>;
}
