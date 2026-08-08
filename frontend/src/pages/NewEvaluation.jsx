import { ArrowRight, ClipboardCheck } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ErrorMessage from '../components/common/ErrorMessage';
import ProcessingState from '../components/evaluation/ProcessingState';
import FileUploadCard from '../components/upload/FileUploadCard';
import { evaluateStudent } from '../services/evaluationApi';

const initialMetadata = { student_id: '', student_name: '', roll_number: '', exam_id: '', subject: '', exam_name: '', semester: '' };

export default function NewEvaluation() {
  const navigate = useNavigate();
  const [files, setFiles] = useState({ questionPaper: null, modelAnswer: null, studentAnswerSheet: null });
  const [metadata, setMetadata] = useState(initialMetadata);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState(false);
  const updateFile = (name) => (file) => setFiles((current) => ({ ...current, [name]: file }));
  const submit = async (event) => {
    event.preventDefault();
    if (!files.questionPaper || !files.modelAnswer || !files.studentAnswerSheet) { setError(new Error('Select a question paper, model answer, and student answer sheet before starting.')); return; }
    setError(null); setProcessing(true);
    try {
      const response = await evaluateStudent({ files, metadata, idempotencyKey: crypto.randomUUID() });
      navigate(`/evaluations/${encodeURIComponent(response.evaluation_id)}`);
    } catch (requestError) {
      if (requestError.evaluationId) navigate(`/evaluations/${encodeURIComponent(requestError.evaluationId)}`);
      else { setError(requestError); setProcessing(false); }
    }
  };
  if (processing) return <ProcessingState />;
  return <form className="page-stack" onSubmit={submit} noValidate><section className="page-intro"><div><p className="eyebrow">Submission</p><h2>Start a new evaluation</h2></div></section>{error && <ErrorMessage error={error} />}<section className="upload-grid"><FileUploadCard id="question-paper" label="Question Paper" helper="PDF or image containing questions and marks." file={files.questionPaper} onChange={updateFile('questionPaper')} /><FileUploadCard id="model-answer" label="Model Answer" helper="PDF or image containing expected answers." file={files.modelAnswer} onChange={updateFile('modelAnswer')} /><FileUploadCard id="student-answer" label="Student Answer Sheet" helper="Handwritten PDF or image for OCR." file={files.studentAnswerSheet} onChange={updateFile('studentAnswerSheet')} /></section><section className="content-section metadata-section"><div className="section-heading"><div><p className="eyebrow">Optional context</p><h2>Student and exam information</h2></div></div><div className="form-grid">{Object.entries({ student_id: 'Student ID', student_name: 'Student Name', roll_number: 'Roll Number', exam_id: 'Exam ID', subject: 'Subject', exam_name: 'Exam Name', semester: 'Semester' }).map(([name, label]) => <label key={name}>{label}<input name={name} value={metadata[name]} onChange={(event) => setMetadata((current) => ({ ...current, [name]: event.target.value }))} /></label>)}</div></section><div className="form-actions"><button type="submit" className="primary-button"><ClipboardCheck aria-hidden="true" />Start Evaluation<ArrowRight aria-hidden="true" /></button></div></form>;
}
