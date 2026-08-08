import { API_BASE_URL } from '../config';

const REQUEST_TIMEOUT_MS = 300000;

export class ApiError extends Error {
  constructor(message, status = 0, code = 'NETWORK_ERROR') {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { ...options, signal: controller.signal });
    const contentType = response.headers.get('content-type') || '';
    const payload = contentType.includes('application/json') ? await response.json() : null;
    if (!response.ok) {
      const apiError = new ApiError(
        payload?.error?.message || friendlyStatusMessage(response.status),
        response.status,
        payload?.error?.code || 'REQUEST_FAILED',
      );
      apiError.evaluationId = payload?.evaluation_id;
      throw apiError;
    }
    return payload;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new ApiError('The request timed out. The evaluation may still be processing; please check history shortly.', 0, 'TIMEOUT');
    }
    if (error instanceof ApiError) throw error;
    throw new ApiError('Unable to reach SmartEval. Check that the backend is running and try again.');
  } finally {
    window.clearTimeout(timeout);
  }
}

function friendlyStatusMessage(status) {
  const messages = {
    400: 'Please review the submitted information and files.',
    404: 'The requested evaluation could not be found.',
    413: 'One of the selected files is too large.',
    422: 'The documents could not be processed. Please check their contents and try again.',
    500: 'SmartEval could not complete the request. Please try again.',
    503: 'Evaluation history is temporarily unavailable. Please try again shortly.',
  };
  return messages[status] || 'The request could not be completed.';
}
