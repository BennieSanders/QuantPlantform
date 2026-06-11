const API_BASE_URL = "";
const TOKEN_STORAGE_KEY = "quant_platform_access_token";

export function getStoredToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export async function registerUser(payload) {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function loginUser(payload) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function getCurrentUser() {
  const response = await fetch(`${API_BASE_URL}/api/users/me`, {
    headers: authHeaders(),
  });
  return parseResponse(response);
}

export async function runBacktest(payload) {
  const response = await fetch(`${API_BASE_URL}/api/backtests`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with ${response.status}`);
  }

  return response.json();
}

export async function createBacktestJob(payload) {
  const response = await fetch(`${API_BASE_URL}/api/backtests/jobs`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function listBacktestJobs(limit = 20) {
  const response = await fetch(`${API_BASE_URL}/api/backtests/jobs?limit=${limit}`, {
    headers: authHeaders(),
  });
  return parseResponse(response);
}

export async function getBacktestJob(id) {
  const response = await fetch(`${API_BASE_URL}/api/backtests/jobs/${id}`, {
    headers: authHeaders(),
  });
  return parseResponse(response);
}

export async function cancelBacktestJob(id) {
  const response = await fetch(`${API_BASE_URL}/api/backtests/jobs/${id}/cancel`, {
    method: "POST",
    headers: authHeaders(),
  });
  return parseResponse(response);
}

export async function retryBacktestJob(id) {
  const response = await fetch(`${API_BASE_URL}/api/backtests/jobs/${id}/retry`, {
    method: "POST",
    headers: authHeaders(),
  });
  return parseResponse(response);
}

export async function listBacktests(limit = 20) {
  const response = await fetch(`${API_BASE_URL}/api/backtests?limit=${limit}`, {
    headers: authHeaders(),
  });
  return parseResponse(response);
}

export async function getBacktest(id) {
  const response = await fetch(`${API_BASE_URL}/api/backtests/${id}`, {
    headers: authHeaders(),
  });
  return parseResponse(response);
}

export async function getMarketKlines(symbol, timeframe, limit = 200) {
  const query = new URLSearchParams({ symbol, timeframe, limit: String(limit) });
  const response = await fetch(`${API_BASE_URL}/api/market/klines?${query}`, {
    headers: authHeaders(),
  });
  return parseResponse(response);
}

export async function syncMarketKlines(payload) {
  const response = await fetch(`${API_BASE_URL}/api/market/sync`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function analyzeBacktest(id) {
  const response = await fetch(`${API_BASE_URL}/api/ai/backtests/${id}/analyze`, {
    method: "POST",
    headers: authHeaders(),
  });
  return parseResponse(response);
}

export async function listBacktestAnalyses(id, limit = 10) {
  const response = await fetch(
    `${API_BASE_URL}/api/ai/backtests/${id}/analyses?limit=${limit}`,
    { headers: authHeaders() },
  );
  return parseResponse(response);
}

export async function listStrategies() {
  const response = await fetch(`${API_BASE_URL}/api/strategies`, {
    headers: authHeaders(),
  });
  return parseResponse(response);
}

export async function createStrategy(payload) {
  const response = await fetch(`${API_BASE_URL}/api/strategies`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function updateStrategy(id, payload) {
  const response = await fetch(`${API_BASE_URL}/api/strategies/${id}`, {
    method: "PUT",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function deleteStrategy(id) {
  const response = await fetch(`${API_BASE_URL}/api/strategies/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with ${response.status}`);
  }
}

function jsonHeaders() {
  return {
    "Content-Type": "application/json",
    ...authHeaders(),
  };
}

function authHeaders() {
  const token = getStoredToken();
  if (!token) return {};
  return {
    Authorization: `Bearer ${token}`,
  };
}

async function parseResponse(response) {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(formatError(errorText, response.status));
  }

  return response.json();
}

function formatError(errorText, status) {
  if (!errorText) return `Request failed with ${status}`;
  try {
    const parsed = JSON.parse(errorText);
    if (typeof parsed.detail === "string") return parsed.detail;
    if (Array.isArray(parsed.detail)) {
      return parsed.detail.map((item) => item.msg ?? JSON.stringify(item)).join("; ");
    }
  } catch {
    return errorText;
  }
  return errorText;
}
