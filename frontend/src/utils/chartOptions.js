import { formatMoney } from "./formatters";

export function buildEquityChartOption(source) {
  const dates = source.equity_curve.map((point) => point.date);
  const values = source.equity_curve.map((point) => point.equity);

  return {
    color: ["#0f766e"],
    tooltip: {
      trigger: "axis",
      valueFormatter: (value) => formatMoney(value),
    },
    grid: {
      left: 56,
      right: 24,
      top: 32,
      bottom: 48,
    },
    xAxis: {
      type: "category",
      data: dates,
      boundaryGap: false,
      axisLabel: { color: "#64748b" },
    },
    yAxis: {
      type: "value",
      scale: true,
      axisLabel: {
        color: "#64748b",
        formatter: (value) => `${Math.round(value)}`,
      },
      splitLine: { lineStyle: { color: "#e2e8f0" } },
    },
    series: [
      {
        name: "权益曲线",
        type: "line",
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3 },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(15, 118, 110, 0.24)" },
              { offset: 1, color: "rgba(15, 118, 110, 0.02)" },
            ],
          },
        },
        data: values,
      },
    ],
  };
}

export function buildMarketChartOption(source) {
  const dates = source.market_klines.map((point) => point.date);
  const candles = source.market_klines.map((point) => [
    point.open,
    point.close,
    point.low,
    point.high,
  ]);
  const volumes = source.market_klines.map((point) => point.volume);
  const closes = source.market_klines.map((point) => point.close);
  const ma7 = calculateMovingAverage(closes, 7);
  const ma25 = calculateMovingAverage(closes, 25);
  const tradeMarks = buildTradeMarks(source.trades ?? [], dates);
  const zoomStart = dates.length > 120 ? Math.max(0, ((dates.length - 120) / dates.length) * 100) : 0;

  return {
    animation: false,
    legend: {
      top: 0,
      left: 12,
      textStyle: { color: "#475569" },
      data: ["K线", "MA7", "MA25", "成交量"],
    },
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
      },
    },
    axisPointer: {
      link: [{ xAxisIndex: "all" }],
    },
    grid: [
      {
        left: 56,
        right: 24,
        top: 42,
        height: "62%",
      },
      {
        left: 56,
        right: 24,
        top: "78%",
        height: "14%",
      },
    ],
    xAxis: [
      {
        type: "category",
        data: dates,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisLabel: { color: "#64748b" },
        splitLine: { show: false },
        min: "dataMin",
        max: "dataMax",
      },
      {
        type: "category",
        gridIndex: 1,
        data: dates,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisLabel: { show: false },
        splitLine: { show: false },
        min: "dataMin",
        max: "dataMax",
      },
    ],
    yAxis: [
      {
        scale: true,
        axisLabel: {
          color: "#64748b",
        },
        splitLine: { lineStyle: { color: "#e2e8f0" } },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      {
        type: "inside",
        xAxisIndex: [0, 1],
        start: zoomStart,
        end: 100,
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: "slider",
        top: "95%",
        start: zoomStart,
        end: 100,
      },
    ],
    series: [
      {
        name: "K线",
        type: "candlestick",
        data: candles,
        itemStyle: {
          color: "#16a34a",
          color0: "#ef4444",
          borderColor: "#16a34a",
          borderColor0: "#ef4444",
        },
        markPoint: {
          symbolSize: 42,
          label: {
            color: "#ffffff",
            fontSize: 11,
            fontWeight: 800,
          },
          data: tradeMarks,
        },
      },
      {
        name: "MA7",
        type: "line",
        data: ma7,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: "#2563eb" },
      },
      {
        name: "MA25",
        type: "line",
        data: ma25,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: "#f59e0b" },
      },
      {
        name: "成交量",
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: "#94a3b8",
        },
      },
    ],
  };
}

function calculateMovingAverage(values, window) {
  return values.map((_, index) => {
    if (index < window - 1) return "-";
    const slice = values.slice(index - window + 1, index + 1);
    return Number((slice.reduce((sum, value) => sum + value, 0) / window).toFixed(4));
  });
}

function buildTradeMarks(trades, dates) {
  return trades
    .map((trade) => {
      const hasDate = dates.includes(trade.date);
      if (!hasDate) return null;
      return {
        name: trade.side,
        coord: [trade.date, trade.price],
        value: trade.side === "buy" ? "B" : "S",
        symbol: "triangle",
        symbolRotate: trade.side === "buy" ? 0 : 180,
        itemStyle: {
          color: trade.side === "buy" ? "#16a34a" : "#dc2626",
        },
      };
    })
    .filter(Boolean);
}
