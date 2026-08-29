import axios from "axios";

// --- Centralized backend URL --------------------------------------------
// Single source of truth for the backend base URL. Override via `.env`
// (REACT_APP_API_URL). No backend URLs are hardcoded in components.
export const API_BASE_URL =
  (process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.trim()) ||
  "http://localhost:8000";

// Sibling borrower portal (Lending-Application). Also configurable via env.
export const USER_PORTAL_URL =
  (process.env.REACT_APP_USER_PORTAL_URL && process.env.REACT_APP_USER_PORTAL_URL.trim()) ||
  "http://localhost:5000";

// localStorage keys for the single, consistent admin-token mechanism.
export const ADMIN_TOKEN_KEY = "admin_token";
export const ADMIN_USER_KEY = "admin_user";
export const ADMIN_ROLE_KEY = "admin_role";

export function getAdminToken() {
  return localStorage.getItem(ADMIN_TOKEN_KEY);
}

export function isAdminAuthed() {
  return getAdminToken() ? true : false;
}

export function setAdminSession(token, admin) {
  localStorage.setItem(ADMIN_TOKEN_KEY, token);
  localStorage.setItem(ADMIN_USER_KEY, JSON.stringify(admin || {}));
  // Every account authenticated through this portal is an admin.
  localStorage.setItem(ADMIN_ROLE_KEY, "admin");
}

export function clearAdminAuth() {
  localStorage.removeItem(ADMIN_TOKEN_KEY);
  localStorage.removeItem(ADMIN_USER_KEY);
  localStorage.removeItem(ADMIN_ROLE_KEY);
}

// Shared axios instance: attaches the admin bearer token on every request and
// clears auth + redirects to the admin login on 401 (expired/invalid token).
const adminApi = axios.create({ baseURL: API_BASE_URL });

adminApi.interceptors.request.use(function (config) {
  var token = getAdminToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = "Bearer " + token;
  }
  return config;
});

adminApi.interceptors.response.use(
  function (response) {
    return response;
  },
  function (error) {
    var url = error.config && error.config.url ? error.config.url : "";
    var isAuthEndpoint = url.indexOf("/api/auth/") !== -1;
    // On an expired/invalid token for a protected call, drop the session and
    // send the admin back to login. The login endpoint reports its own errors
    // inline (so a wrong password does not trigger a redirect).
    if (error.response && error.response.status === 401 && !isAuthEndpoint) {
      clearAdminAuth();
      if (window.location.pathname !== "/admin-login") {
        window.location = "/admin-login";
      }
    }
    return Promise.reject(error);
  }
);

export { adminApi };
export default adminApi;
