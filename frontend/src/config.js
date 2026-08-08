export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
export const ACCEPTED_FILE_TYPES = ['application/pdf', 'image/png', 'image/jpeg'];
export const ACCEPTED_FILE_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg'];
export const MAX_UPLOAD_SIZE_MB = 20;
