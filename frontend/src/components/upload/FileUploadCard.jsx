import { FileText, Upload, X } from 'lucide-react';
import { useRef, useState } from 'react';
import { ACCEPTED_FILE_EXTENSIONS, ACCEPTED_FILE_TYPES, MAX_UPLOAD_SIZE_MB } from '../../config';
import { formatFileSize } from '../../utils/formatters';

export default function FileUploadCard({ id, label, helper, file, onChange }) {
  const input = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState(null);

  const chooseFile = (candidate) => {
    if (!candidate) return;
    const extension = candidate.name.split('.').pop().toLowerCase();
    if ((!ACCEPTED_FILE_TYPES.includes(candidate.type) && !ACCEPTED_FILE_EXTENSIONS.includes(extension)) || candidate.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024) {
      setError(`Choose a PDF, PNG, JPG, or JPEG under ${MAX_UPLOAD_SIZE_MB} MB.`);
      return;
    }
    setError(null);
    onChange(candidate);
  };

  return <section className={`upload-card ${dragging ? 'dragging' : ''}`} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files[0]); }}>
    <div className="upload-heading"><FileText aria-hidden="true" /><div><h2>{label}</h2><p>{helper}</p></div></div>
    {file ? <div className="selected-file"><div><strong>{file.name}</strong><span>{file.type || 'Document'} ({formatFileSize(file.size)})</span></div><button className="icon-button" type="button" aria-label={`Remove ${label}`} onClick={() => onChange(null)}><X /></button></div> : <div className="drop-zone"><Upload aria-hidden="true" /><p>Drop a file here</p><button type="button" className="secondary-button" onClick={() => input.current?.click()}>Browse files</button></div>}
    <input ref={input} id={id} className="visually-hidden" type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" onChange={(event) => chooseFile(event.target.files?.[0])} />
    {error && <p className="field-error" role="alert">{error}</p>}
  </section>;
}
