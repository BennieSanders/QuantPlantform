<template>
  <main class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">Q</span>
        <div>
          <strong>量化交易平台</strong>
          <span>Crypto Lab</span>
        </div>
      </div>

      <nav class="nav-list">
        <button
          v-for="item in navItems"
          :key="item.key"
          :class="{ active: activeView === item.key }"
          type="button"
          @click="activeView = item.key"
        >
          <span>{{ item.icon }}</span>
          {{ item.label }}
        </button>
      </nav>
    </aside>

    <section class="main-panel">
      <header class="topbar">
        <div>
          <p class="eyebrow">{{ currentView.eyebrow }}</p>
          <h1>{{ currentView.title }}</h1>
        </div>
        <div class="status-pill">现货做多 · CSV 数据</div>
      </header>

      <section v-if="activeView === 'dashboard'" class="view-stack">
        <div class="summary-grid">
          <article class="metric">
            <span>最近总收益率</span>
            <strong>{{ formatPercent(result?.metrics.total_return) }}</strong>
          </article>
          <article class="metric">
            <span>年化收益率</span>
            <strong>{{ formatPercent(result?.metrics.annualized_return) }}</strong>
          </article>
          <article class="metric">
            <span>最终权益</span>
            <strong>{{ formatMoney(result?.metrics.final_equity) }}</strong>
          </article>
          <article class="metric">
            <span>夏普比率</span>
            <strong>{{ formatNumber(result?.metrics.sharpe_ratio) }}</strong>
          </article>
        </div>

        <section class="content-card">
          <div class="section-heading">
            <h2>最近回测权益曲线</h2>
            <span>{{ result?.symbol ?? "BTCUSDT" }} · {{ result?.timeframe ?? "1d" }}</span>
          </div>
          <div ref="dashboardChartRef" class="chart"></div>
        </section>

        <section class="content-card">
          <div class="section-heading">
            <h2>最近回测记录</h2>
            <span>{{ recentBacktests.length }} 条</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>时间</th>
                  <th>标的</th>
                  <th>策略</th>
                  <th>收益率</th>
                  <th>最大回撤</th>
                  <th>最终权益</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="record in recentBacktests" :key="record.id">
                  <td>{{ formatDateTime(record.created_at) }}</td>
                  <td>{{ record.symbol }} · {{ record.timeframe }}</td>
                  <td>{{ record.strategy_name }}</td>
                  <td>{{ formatPercent(record.metrics.total_return) }}</td>
                  <td>{{ formatPercent(record.metrics.max_drawdown) }}</td>
                  <td>{{ formatMoney(record.metrics.final_equity) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </section>

      <section v-if="activeView === 'history'" class="history-layout">
        <section class="content-card">
          <div class="section-heading">
            <h2>回测历史</h2>
            <button class="secondary-button" type="button" @click="refreshBacktests">刷新</button>
          </div>
          <div class="table-wrap history-table">
            <table>
              <thead>
                <tr>
                  <th>时间</th>
                  <th>标的</th>
                  <th>策略</th>
                  <th>收益率</th>
                  <th>最大回撤</th>
                  <th>夏普</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="record in recentBacktests"
                  :key="record.id"
                  :class="{ selected: selectedHistoryId === record.id }"
                  class="clickable-row"
                  @click="loadBacktestRecord(record.id)"
                >
                  <td>{{ formatDateTime(record.created_at) }}</td>
                  <td>{{ record.symbol }} · {{ record.timeframe }}</td>
                  <td>{{ record.strategy_name }}</td>
                  <td>{{ formatPercent(record.metrics.total_return) }}</td>
                  <td>{{ formatPercent(record.metrics.max_drawdown) }}</td>
                  <td>{{ formatNumber(record.metrics.sharpe_ratio) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="content-card history-detail">
          <div class="section-heading">
            <h2>历史详情</h2>
            <span>{{ selectedHistoryResult?.backtest_id ?? "请选择一条记录" }}</span>
          </div>

          <div class="summary-grid">
            <article class="metric">
              <span>总收益率</span>
              <strong>{{ formatPercent(selectedHistoryResult?.metrics.total_return) }}</strong>
            </article>
            <article class="metric">
              <span>年化收益率</span>
              <strong>{{ formatPercent(selectedHistoryResult?.metrics.annualized_return) }}</strong>
            </article>
            <article class="metric">
              <span>最大回撤</span>
              <strong>{{ formatPercent(selectedHistoryResult?.metrics.max_drawdown) }}</strong>
            </article>
            <article class="metric">
              <span>交易次数</span>
              <strong>{{ selectedHistoryResult?.metrics.trade_count ?? "-" }}</strong>
            </article>
          </div>

          <div ref="historyChartRef" class="chart"></div>
          <TradeTable :trades="selectedHistoryResult?.trades ?? []" />
        </section>
      </section>

      <section v-if="activeView === 'backtest'" class="workspace">
        <aside class="control-panel">
          <form class="form-grid" @submit.prevent="submitBacktest">
            <label>
              交易标的
              <select v-model="form.symbol">
                <option value="BTCUSDT">BTCUSDT</option>
                <option value="ETHUSDT">ETHUSDT</option>
              </select>
            </label>

            <label>
              策略
              <select v-model="form.strategyId" @change="syncSelectedStrategyFromForm">
                <option v-for="strategy in strategies" :key="strategy.id" :value="strategy.id">
                  {{ strategy.name }}
                </option>
              </select>
            </label>

            <label>
              K 线周期
              <select v-model="form.timeframe">
                <option value="1d">日线</option>
              </select>
            </label>

            <label>
              开始日期
              <input v-model="form.startDate" type="date" />
            </label>

            <label>
              结束日期
              <input v-model="form.endDate" type="date" />
            </label>

            <label>
              初始资金
              <input v-model.number="form.initialCash" min="1" step="100" type="number" />
            </label>

            <label v-for="field in strategyParamFields" :key="field.key">
              {{ field.label }}
              <input
                v-model.number="form.params[field.key]"
                :min="field.min"
                :step="field.step"
                type="number"
              />
            </label>

            <button :disabled="loading" type="submit">
              {{ loading ? "回测中..." : "运行回测" }}
            </button>
          </form>

          <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
        </aside>

        <section class="result-panel">
          <div class="summary-grid">
            <article class="metric">
              <span>总收益率</span>
              <strong>{{ formatPercent(result?.metrics.total_return) }}</strong>
            </article>
            <article class="metric">
              <span>年化收益率</span>
              <strong>{{ formatPercent(result?.metrics.annualized_return) }}</strong>
            </article>
            <article class="metric">
              <span>最终权益</span>
              <strong>{{ formatMoney(result?.metrics.final_equity) }}</strong>
            </article>
            <article class="metric">
              <span>夏普比率</span>
              <strong>{{ formatNumber(result?.metrics.sharpe_ratio) }}</strong>
            </article>
          </div>

          <div ref="backtestChartRef" class="chart"></div>

          <TradeTable :trades="result?.trades ?? []" />
        </section>
      </section>

      <section v-if="activeView === 'strategies'" class="strategy-layout">
        <section class="content-card strategy-list">
          <div class="section-heading">
            <h2>策略列表</h2>
            <button class="secondary-button" type="button" @click="newStrategy">新建策略</button>
          </div>

          <button
            v-for="strategy in strategies"
            :key="strategy.id"
            :class="{ active: selectedStrategy?.id === strategy.id }"
            class="strategy-item"
            type="button"
            @click="selectStrategy(strategy)"
          >
            <span>
              <strong>{{ strategy.name }}</strong>
              <button class="link-button" type="button" @click.stop="copyStrategy(strategy)">复制</button>
            </span>
            <small>{{ formatStrategyType(strategy.strategy_type) }} · {{ formatStatus(strategy.status) }}</small>
          </button>
        </section>

        <section class="content-card strategy-editor">
          <div class="section-heading">
            <h2>策略编辑</h2>
            <span>{{ selectedStrategy?.id ?? "未保存" }}</span>
          </div>

          <form class="editor-grid" @submit.prevent="saveStrategy">
            <label>
              策略名称
              <input v-model="strategyDraft.name" />
            </label>

            <label>
              策略说明
              <input v-model="strategyDraft.description" />
            </label>

            <label>
              状态
              <select v-model="strategyDraft.status">
                <option value="draft">草稿</option>
                <option value="active">启用</option>
                <option value="archived">归档</option>
              </select>
            </label>

            <label>
              默认参数 JSON
              <textarea v-model="strategyDraft.paramsText" class="params-editor"></textarea>
            </label>

            <label class="code-field">
              策略代码
              <textarea v-model="strategyDraft.code" class="code-editor" spellcheck="false"></textarea>
            </label>

            <div class="editor-actions">
              <button :disabled="strategySaving" type="submit">
                {{ strategySaving ? "保存中..." : "保存策略" }}
              </button>
              <button
                v-if="selectedStrategy?.strategy_type === 'builtin'"
                class="secondary-button"
                type="button"
                @click="copyStrategy(selectedStrategy)"
              >
                复制为自定义策略
              </button>
              <button
                v-if="selectedStrategy && selectedStrategy.strategy_type !== 'builtin'"
                class="danger-button"
                type="button"
                @click="removeSelectedStrategy"
              >
                删除策略
              </button>
            </div>
          </form>

          <p v-if="strategyMessage" class="success-message">{{ strategyMessage }}</p>
          <p v-if="strategyError" class="error-message">{{ strategyError }}</p>
        </section>
      </section>
    </section>
  </main>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { createStrategy, deleteStrategy, getBacktest, listBacktests, listStrategies, runBacktest, updateStrategy } from "./api";

const navItems = [
  { key: "dashboard", label: "Dashboard", title: "系统总览", eyebrow: "Overview", icon: "□" },
  { key: "backtest", label: "回测中心", title: "回测中心", eyebrow: "Backtest", icon: "◧" },
  { key: "history", label: "回测历史", title: "回测历史", eyebrow: "History", icon: "≋" },
  { key: "strategies", label: "策略管理", title: "策略管理", eyebrow: "Strategy CRUD", icon: "⌘" },
];

const DEFAULT_CUSTOM_STRATEGY_CODE = `def generate_signals(klines, params):
    short_window = int(params.get("short_window", 7))
    long_window = int(params.get("long_window", 30))
    if len(klines) < long_window + 1:
        return []

    closes = [kline.close for kline in klines]
    prev_short = sum(closes[-short_window - 1:-1]) / short_window
    prev_long = sum(closes[-long_window - 1:-1]) / long_window
    curr_short = sum(closes[-short_window:]) / short_window
    curr_long = sum(closes[-long_window:]) / long_window

    if prev_short <= prev_long and curr_short > curr_long:
        return [{"date": klines[-1].date, "action": "buy"}]
    if prev_short >= prev_long and curr_short < curr_long:
        return [{"date": klines[-1].date, "action": "sell"}]
    return []
`;

const TradeTable = defineComponent({
  props: {
    trades: {
      type: Array,
      required: true,
    },
  },
  setup(props) {
    return () =>
      h("section", { class: "table-section" }, [
        h("div", { class: "section-heading" }, [
          h("h2", "交易记录"),
          h("span", `${props.trades.length} 条记录`),
        ]),
        h("div", { class: "table-wrap" }, [
          h("table", [
            h("thead", [
              h("tr", [
                h("th", "日期"),
                h("th", "方向"),
                h("th", "价格"),
                h("th", "数量"),
                h("th", "手续费"),
              ]),
            ]),
            h(
              "tbody",
              props.trades.map((trade) =>
                h("tr", { key: `${trade.date}-${trade.side}` }, [
                  h("td", trade.date),
                  h("td", [
                    h("span", { class: ["side", trade.side] }, formatSide(trade.side)),
                  ]),
                  h("td", formatMoney(trade.price)),
                  h("td", trade.quantity.toFixed(6)),
                  h("td", formatMoney(trade.fee)),
                ]),
              ),
            ),
          ]),
        ]),
      ]);
  },
});

const activeView = ref("dashboard");
const currentView = computed(
  () => navItems.find((item) => item.key === activeView.value) ?? navItems[0],
);
const selectedFormStrategy = computed(
  () => strategies.value.find((strategy) => strategy.id === form.strategyId) ?? null,
);
const strategyParamFields = computed(() =>
  Object.entries(selectedFormStrategy.value?.default_params ?? {}).map(([key, value]) => ({
    key,
    label: formatParamLabel(key),
    min: getParamMin(key),
    step: Number.isInteger(value) ? 1 : 0.1,
  })),
);

const dashboardChartRef = ref(null);
const backtestChartRef = ref(null);
const historyChartRef = ref(null);
const loading = ref(false);
const errorMessage = ref("");
const result = ref(null);
const recentBacktests = ref([]);
const selectedHistoryId = ref("");
const selectedHistoryResult = ref(null);
const strategies = ref([]);
const selectedStrategy = ref(null);
const strategySaving = ref(false);
const strategyMessage = ref("");
const strategyError = ref("");
let dashboardChart = null;
let backtestChart = null;
let historyChart = null;

const form = reactive({
  symbol: "BTCUSDT",
  strategyId: "ma-cross-default",
  timeframe: "1d",
  startDate: "2024-01-01",
  endDate: "2024-12-31",
  initialCash: 10000,
  params: {},
});

const strategyDraft = reactive({
  name: "",
  description: "",
  status: "draft",
  code: "",
  paramsText: "{}",
});

onMounted(async () => {
  await refreshStrategies();
  await submitBacktest();
  window.addEventListener("resize", resizeCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  dashboardChart?.dispose();
  backtestChart?.dispose();
  historyChart?.dispose();
});

watch(activeView, async () => {
  await nextTick();
  ensureCharts();
  renderCharts();
});

async function refreshStrategies() {
  strategies.value = await listStrategies();
  if (!selectedStrategy.value && strategies.value.length > 0) {
    selectStrategy(strategies.value[0]);
  }
}

async function submitBacktest() {
  errorMessage.value = "";
  loading.value = true;

  try {
    const strategy = strategies.value.find((item) => item.id === form.strategyId) ?? selectedStrategy.value;
    const payload = {
      asset_class: "crypto",
      market_type: "spot",
      symbol: form.symbol,
      timeframe: form.timeframe,
      position_mode: "long_only",
      strategy: getStrategyKind(strategy),
      strategy_id: form.strategyId,
      start_date: form.startDate,
      end_date: form.endDate,
      initial_cash: form.initialCash,
      params: { ...form.params },
    };

    result.value = await runBacktest(payload);
    selectedHistoryId.value = result.value.backtest_id;
    selectedHistoryResult.value = result.value;
    await refreshBacktests();
    await nextTick();
    ensureCharts();
    renderCharts();
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    loading.value = false;
  }
}

async function refreshBacktests() {
  recentBacktests.value = await listBacktests(20);
}

async function loadBacktestRecord(id) {
  selectedHistoryId.value = id;
  selectedHistoryResult.value = await getBacktest(id);
  await nextTick();
  ensureCharts();
  renderCharts();
}

function selectStrategy(strategy) {
  selectedStrategy.value = strategy;
  strategyDraft.name = strategy.name;
  strategyDraft.description = strategy.description;
  strategyDraft.status = strategy.status;
  strategyDraft.code = strategy.code;
  strategyDraft.paramsText = JSON.stringify(strategy.default_params, null, 2);
  form.strategyId = strategy.id;
  form.params = { ...strategy.default_params };
}

function syncSelectedStrategyFromForm() {
  const strategy = strategies.value.find((item) => item.id === form.strategyId);
  if (strategy) selectStrategy(strategy);
}

function newStrategy() {
  selectedStrategy.value = null;
  strategyDraft.name = "新策略";
  strategyDraft.description = "";
  strategyDraft.status = "draft";
  strategyDraft.code = DEFAULT_CUSTOM_STRATEGY_CODE;
  strategyDraft.paramsText = JSON.stringify({ short_window: 7, long_window: 30 }, null, 2);
  strategyMessage.value = "";
  strategyError.value = "";
}

function copyStrategy(strategy) {
  selectedStrategy.value = null;
  strategyDraft.name = `${strategy.name} 副本`;
  strategyDraft.description = strategy.description;
  strategyDraft.status = "draft";
  strategyDraft.code = strategy.strategy_type === "builtin" ? DEFAULT_CUSTOM_STRATEGY_CODE : strategy.code;
  strategyDraft.paramsText = JSON.stringify(strategy.default_params, null, 2);
  strategyMessage.value = "已复制为未保存的自定义策略";
  strategyError.value = "";
}

async function saveStrategy() {
  strategySaving.value = true;
  strategyMessage.value = "";
  strategyError.value = "";

  try {
    const payload = {
      name: strategyDraft.name,
      description: strategyDraft.description,
      strategy_type: "custom_code",
      code: strategyDraft.code,
      default_params: JSON.parse(strategyDraft.paramsText || "{}"),
      status: strategyDraft.status,
    };

    const saved = selectedStrategy.value
      ? await updateStrategy(selectedStrategy.value.id, payload)
      : await createStrategy(payload);

    await refreshStrategies();
    const fresh = strategies.value.find((strategy) => strategy.id === saved.id);
    if (fresh) selectStrategy(fresh);
    strategyMessage.value = "策略已保存";
  } catch (error) {
    strategyError.value = error.message;
  } finally {
    strategySaving.value = false;
  }
}

async function removeSelectedStrategy() {
  if (!selectedStrategy.value) return;

  strategyError.value = "";
  strategyMessage.value = "";

  try {
    await deleteStrategy(selectedStrategy.value.id);
    selectedStrategy.value = null;
    await refreshStrategies();
    strategyMessage.value = "策略已删除";
  } catch (error) {
    strategyError.value = error.message;
  }
}

function ensureCharts() {
  if (dashboardChartRef.value && !dashboardChart) {
    dashboardChart = echarts.init(dashboardChartRef.value);
  }
  if (backtestChartRef.value && !backtestChart) {
    backtestChart = echarts.init(backtestChartRef.value);
  }
  if (historyChartRef.value && !historyChart) {
    historyChart = echarts.init(historyChartRef.value);
  }
}

function renderCharts() {
  renderChart(dashboardChart, result.value);
  renderChart(backtestChart, result.value);
  renderChart(historyChart, selectedHistoryResult.value);
}

function renderChart(chart, source) {
  if (!chart || !source) return;

  const dates = source.equity_curve.map((point) => point.date);
  const values = source.equity_curve.map((point) => point.equity);

  chart.setOption({
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
  });
}

function resizeCharts() {
  dashboardChart?.resize();
  backtestChart?.resize();
  historyChart?.resize();
}

function formatPercent(value) {
  if (value === undefined || value === null) return "-";
  return `${(value * 100).toFixed(2)}%`;
}

function formatMoney(value) {
  if (value === undefined || value === null) return "-";
  return `${Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} USDT`;
}

function formatNumber(value) {
  if (value === undefined || value === null) return "-";
  return Number(value).toFixed(2);
}

function formatDateTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString(undefined, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatSide(side) {
  if (side === "buy") return "买入";
  if (side === "sell") return "卖出";
  return side;
}

function formatStrategyType(type) {
  if (type === "builtin") return "内置";
  if (type === "custom_code") return "自定义";
  return type;
}

function formatStatus(status) {
  if (status === "active") return "启用";
  if (status === "draft") return "草稿";
  if (status === "archived") return "归档";
  return status;
}

function getStrategyKind(strategy) {
  if (strategy?.strategy_type === "custom_code") return "custom_code";
  if (strategy?.id === "rsi-reversal-default") return "rsi_reversal";
  return "ma_cross";
}

function formatParamLabel(key) {
  const labels = {
    short_window: "短均线周期",
    long_window: "长均线周期",
    period: "RSI 周期",
    oversold: "超卖阈值",
    overbought: "超买阈值",
  };
  return labels[key] ?? key;
}

function getParamMin(key) {
  if (key === "overbought" || key === "oversold") return 1;
  return 2;
}
</script>
