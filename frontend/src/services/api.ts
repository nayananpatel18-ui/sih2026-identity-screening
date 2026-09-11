import axios from 'axios';
import { HealthStatus, CanonicalDocumentSample, MultimodalScreeningResult, UploadFileResponse } from '../types';
import { getCurrentFirebaseUser } from './firebase';

const API_BASE_URL = '/api';

export class AuthenticationRequiredError extends Error {
  constructor(message = 'Sign in is required before using this protected action.') {
    super(message);
    this.name = 'AuthenticationRequiredError';
  }
}

async function protectedHeaders(): Promise<Record<string, string>> {
  const user = getCurrentFirebaseUser();
  if (!user) throw new AuthenticationRequiredError();
  try {
    return { Authorization: `Bearer ${await user.getIdToken()}` };
  } catch {
    throw new AuthenticationRequiredError('Your sign-in session has expired. Please sign in again.');
  }
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof AuthenticationRequiredError) return error.message;
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) return 'Your session is invalid or has expired. Please sign in again.';
    if (error.response?.status === 503) return 'Firebase authentication is unavailable on the backend. Check its Firebase Admin configuration.';
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
  }
  return fallback;
}

export const api = {
  async checkHealth(): Promise<HealthStatus> {
    const res = await axios.get<HealthStatus>(`${API_BASE_URL}/health`);
    return res.data;
  },

  async listSamples(dataset: string = 'synthetic'): Promise<string[]> {
    const res = await axios.get<string[]>(`${API_BASE_URL}/samples?dataset=${dataset}`);
    return res.data;
  },

  async getSample(sampleId: string, dataset: string = 'synthetic'): Promise<CanonicalDocumentSample> {
    const res = await axios.get<CanonicalDocumentSample>(`${API_BASE_URL}/samples/${sampleId}?dataset=${dataset}`);
    return res.data;
  },

  async runScreening(sampleId: string, dataset: string = 'synthetic'): Promise<MultimodalScreeningResult> {
    const res = await axios.post<MultimodalScreeningResult>(`${API_BASE_URL}/screenings/run`, {
      sample_id: sampleId,
      dataset,
    }, {
      headers: await protectedHeaders(),
    });
    return res.data;
  },

  async uploadFile(file: File, docType: string = 'primary_document'): Promise<UploadFileResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await axios.post<UploadFileResponse>(`${API_BASE_URL}/upload?doc_type=${encodeURIComponent(docType)}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...(await protectedHeaders()),
      },
    });

    return res.data;
  },
};
