const API_BASE_URL = "";

export async function runBacktest(payload) {
  const response = await fetch(`${API_BASE_URL}/api/backtests`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with ${response.status}`);
  }

  return response.json();
}

export async function listBacktests(limit = 20) {
  const response = await fetch(`${API_BASE_URL}/api/backtests?limit=${limit}`);
  return parseResponse(response);
}

export async function getBacktest(id) {
  const response = await fetch(`${API_BASE_URL}/api/backtests/${id}`);
  return parseResponse(response);
}

export async function listStrategies() {
  const response = await fetch(`${API_BASE_URL}/api/strategies`);
  return parseResponse(response);
}

export async function createStrategy(payload) {
  const response = await fetch(`${API_BASE_URL}/api/strategies`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function updateStrategy(id, payload) {
  const response = await fetch(`${API_BASE_URL}/api/strategies/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function deleteStrategy(id) {
  const response = await fetch(`${API_BASE_URL}/api/strategies/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with ${response.status}`);
  }
}

async function parseResponse(response) {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with ${response.status}`);
  }

  return response.json();
}
