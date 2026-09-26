import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('wound_ai_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // When sending FormData, remove the default Content-Type so axios
    // can auto-set multipart/form-data with the correct boundary.
    // Without this, the default 'application/json' header causes FastAPI
    // to reject the request with 422 Unprocessable Content.
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
      // Also delete from common/default headers if present
      if (config.headers.common) delete config.headers.common['Content-Type'];
      if (config.headers.post) delete config.headers.post['Content-Type'];
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('wound_ai_token');
      localStorage.removeItem('wound_ai_user');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
