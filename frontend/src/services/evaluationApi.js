import { request } from './api';

export function evaluateStudent({ files, metadata, idempotencyKey }) {
  const formData = new FormData();
  formData.append('question_paper', files.questionPaper);
  formData.append('model_answer', files.modelAnswer);
  formData.append('student_answer_sheet', files.studentAnswerSheet);
  Object.entries(metadata).forEach(([key, value]) => {
    if (value?.trim()) formData.append(key, value.trim());
  });
  return request('/api/v1/evaluate', {
    method: 'POST',
    headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined,
    body: formData,
  });
}

export function getEvaluation(evaluationId) {
  return request(`/api/v1/evaluations/${encodeURIComponent(evaluationId)}`);
}

export function getEvaluations({ page = 1, pageSize = 20, studentId, examId, status } = {}) {
  const parameters = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (studentId) parameters.set('student_id', studentId);
  if (examId) parameters.set('exam_id', examId);
  if (status) parameters.set('status', status);
  return request(`/api/v1/evaluations?${parameters}`);
}

export function getStudentEvaluations(studentId, { page = 1, pageSize = 20, examId } = {}) {
  const parameters = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (examId) parameters.set('exam_id', examId);
  return request(`/api/v1/students/${encodeURIComponent(studentId)}/evaluations?${parameters}`);
}

export function getExamEvaluations(examId, { page = 1, pageSize = 20 } = {}) {
  return request(`/api/v1/exams/${encodeURIComponent(examId)}/evaluations?page=${page}&page_size=${pageSize}`);
}
