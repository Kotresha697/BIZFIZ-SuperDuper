import axios from "axios";

// --- Centralized backend URL --------------------------------------------
// Single source of truth for the backend base URL. Override in `.env` via
// REACT_APP_API_URL (see .env). No backend URLs are hardcoded elsewhere.
export const API_BASE_URL =
  (process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.trim()) ||
  "http://127.0.0.1:8000";

// localStorage keys for the single, consistent client-token mechanism.
export const CLIENT_TOKEN_KEY = "client_token";
export const CLIENT_USER_KEY = "client_user";
export const CLIENT_ROLE_KEY = "client_role";

export function getClientToken() {
  return localStorage.getItem(CLIENT_TOKEN_KEY);
}

export function setClientSession(token, user) {
  localStorage.setItem(CLIENT_TOKEN_KEY, token);
  localStorage.setItem(CLIENT_USER_KEY, JSON.stringify(user || {}));
  // Every account authenticated through this portal is a client.
  localStorage.setItem(CLIENT_ROLE_KEY, "client");
}

export function clearClientAuth() {
  localStorage.removeItem(CLIENT_TOKEN_KEY);
  localStorage.removeItem(CLIENT_USER_KEY);
  localStorage.removeItem(CLIENT_ROLE_KEY);
}

// Shared axios instance: attaches the bearer token on every request and
// clears auth + redirects to the login screen on 401 (expired/invalid token).
const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use(function (config) {
  var token = getClientToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = "Bearer " + token;
  }
  return config;
});

api.interceptors.response.use(
  function (response) {
    return response;
  },
  function (error) {
    var isAuthEndpoint =
      error.config && error.config.url && error.config.url.indexOf("/api/auth/") !== -1;
    // On an expired/invalid token for a protected call, drop the session and
    // send the user back to login. Auth endpoints handle their own errors
    // inline (so a wrong password does not trigger a redirect).
    if (error.response && error.response.status === 401 && !isAuthEndpoint) {
      clearClientAuth();
      if (window.location.pathname !== "/login") {
        window.location = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export { api };
export default api;
