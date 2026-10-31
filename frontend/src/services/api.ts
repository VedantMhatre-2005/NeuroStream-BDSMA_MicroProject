import axios from 'axios';
import {
  SystemStatus,
  ResourceUsage,
  DatasetStatus,
  Participant,
  StreamingStatus,
  ModelStatus,
  ModelMetrics,
  AnalyticsOverview,
  HiveQueryResult,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export const systemApi = {
  getStatus: () => api.get<SystemStatus>('/system/status').then(r => r.data),
  getResources: () => api.get<ResourceUsage>('/system/resources').then(r => r.data),
  getHealth: () => api.get('/health').then(r => r.data),
};

export const datasetApi = {
  getStatus: () => api.get<DatasetStatus>('/dataset/status').then(r => r.data),
  getParticipants: () => api.get<Participant[]>('/dataset/participants').then(r => r.data),
  getRecordings: () => api.get('/dataset/recordings').then(r => r.data),
  getSampleSignal: (params: {
    recording_id?: string;
    channels?: string;
    start_sec?: number;
    duration_sec?: number;
    filtered?: boolean;
    downsample_factor?: number;
  }) => api.get('/dataset/sample-signal', { params }).then(r => r.data),
};

export const streamingApi = {
  getStatus: () => api.get<StreamingStatus>('/streaming/status').then(r => r.data),
  getRecentPredictions: () => api.get<any[]>('/streaming/recent-predictions').then(r => r.data),
  start: (params: { participant_id?: string; recording_id?: string; replay_speed?: number; from_beginning?: boolean }) =>
    api.post('/streaming/start', params).then(r => r.data),
  pause: () => api.post('/streaming/pause').then(r => r.data),
  resume: () => api.post('/streaming/resume').then(r => r.data),
  stop: () => api.post('/streaming/stop').then(r => r.data),
  setSpeed: (speed: number) => api.post('/streaming/speed', { speed }).then(r => r.data),
  replay: (params: { participant_id?: string; recording_id?: string; replay_speed?: number }) =>
    api.post('/streaming/replay', params).then(r => r.data),
};

export const modelApi = {
  getStatus: () => api.get<ModelStatus>('/model/status').then(r => r.data),
  getMetrics: () => api.get<ModelMetrics>('/model/metrics').then(r => r.data),
  getConfusionMatrix: () => api.get('/model/confusion-matrix').then(r => r.data),
  getFeatures: () => api.get('/model/features').then(r => r.data),
  train: (params: { n_estimators?: number; test_size?: number; random_state?: number }) =>
    api.post('/model/train', params).then(r => r.data),
};

export const analyticsApi = {
  getOverview: () => api.get<AnalyticsOverview>('/analytics/overview').then(r => r.data),
  getBrainStates: () => api.get('/analytics/brain-states').then(r => r.data),
  getChannelActivity: (limit = 20) => api.get('/analytics/channel-activity', { params: { limit } }).then(r => r.data),
  getBandPower: () => api.get('/analytics/band-power').then(r => r.data),
  getParticipants: () => api.get('/analytics/participants').then(r => r.data),
  getTimeline: (limit = 30) => api.get('/analytics/timeline', { params: { limit } }).then(r => r.data),
  getRecordings: () => api.get('/analytics/recordings').then(r => r.data),
};

export const hiveApi = {
  getStatus: () => api.get('/hive/status').then(r => r.data),
  getTables: () => api.get('/hive/tables').then(r => r.data),
  getSchema: (table: string) => api.get(`/hive/schema/${table}`).then(r => r.data),
  executeQuery: (query: string) => api.post<HiveQueryResult>('/hive/query', { query }).then(r => r.data),
};

export default api;

