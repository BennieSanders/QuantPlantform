export function formatPercent(value) {
  if (value === undefined || value === null) return "-";
  return `${(value * 100).toFixed(2)}%`;
}

export function formatMoney(value) {
  if (value === undefined || value === null) return "-";
  return `${Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} USDT`;
}

export function formatNumber(value) {
  if (value === undefined || value === null) return "-";
  return Number(value).toFixed(2);
}

export function formatDateTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString(undefined, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatSide(side) {
  if (side === "buy") return "买入";
  if (side === "sell") return "卖出";
  return side;
}

export function formatStrategyType(type) {
  if (type === "builtin") return "内置";
  if (type === "custom_code") return "自定义";
  return type;
}

export function formatStatus(status) {
  if (status === "active") return "启用";
  if (status === "draft") return "草稿";
  if (status === "archived") return "归档";
  return status;
}

export function formatParamLabel(key) {
  const labels = {
    short_window: "短均线周期",
    long_window: "长均线周期",
    period: "RSI 周期",
    oversold: "超卖阈值",
    overbought: "超买阈值",
  };
  return labels[key] ?? key;
}

export function getParamMin(key) {
  if (key === "overbought" || key === "oversold") return 1;
  return 2;
}
