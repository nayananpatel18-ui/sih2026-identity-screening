import axios from 'axios';
import { HealthStatus, CanonicalDocumentSample, MultimodalScreeningResult, UploadFileResponse } from '../types';

const API_BASE_URL = '/api';

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
    });
    return res.data;
  },

  async uploadFile(file: File, docType: string = 'primary_document'): Promise<UploadFileResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await axios.post<UploadFileResponse>(`${API_BASE_URL}/upload?doc_type=${encodeURIComponent(docType)}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return res.data;
  },
};
