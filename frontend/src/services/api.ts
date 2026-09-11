import axios from 'axios';
import { HealthStatus, CanonicalDocumentSample } from '../types';

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
  }
};
