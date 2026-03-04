import axios from 'axios';

// Use external URL if provided (for Render and other hosting platforms), else fallback to local proxy
const API_BASE = import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api';

const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Feedback
export const submitFeedback = (text, source = 'manual') =>
    api.post('/feedback/', { text, source });

export const uploadCSV = (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/feedback/csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};

export const getFeedbacks = (params = {}) =>
    api.get('/feedback/', { params });

export const analyzeFeedback = (text) =>
    api.post('/feedback/analyze', { text });

export const correctFeedback = (id, correction) =>
    api.put(`/feedback/${id}/correct`, correction);

// Analytics
export const getOverview = () => api.get('/analytics/overview');
export const getTrends = (days = 30) => api.get('/analytics/trends', { params: { days } });
export const getInsights = () => api.get('/analytics/insights');
export const getModelInfo = () => api.get('/analytics/model-info');

export default api;
