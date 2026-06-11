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

      <div class="account-box">
        <span>{{ currentUser?.username ?? "未登录" }}</span>
        <button class="link-button sidebar-link" type="button" @click="activeView = 'account'">
          账户
        </button>
      </div>
    </aside>

    <section class="main-panel">
      <header class="topbar">
        <div>
          <p class="eyebrow">{{ currentView.eyebrow }}</p>
          <h1>{{ currentView.title }}</h1>
        </div>
        <div class="topbar-actions">
          <div class="status-pill">现货做多 · 历史回测 + 实时行情</div>
          <button v-if="currentUser" class="secondary-button" type="button" @click="logout">
            退出
          </button>
        </div>
      </header>

      <AccountView
        v-if="activeView === 'account'"
        :auth-token="authToken"
        :current-user="currentUser"
        :error="authError"
        :form="authForm"
        :loading="authLoading"
        :message="authMessage"
        :mode="authMode"
        @submit-auth="submitAuth"
        @toggle-mode="toggleAuthMode"
        @update-form="updateAuthForm"
      />

      <DashboardView
        v-if="activeView === 'dashboard'"
        :recent-backtests="recentBacktests"
        :result="result"
        @chart-ready="setDashboardChartRef"
      />

      <HistoryView
        v-if="activeView === 'history'"
        :recent-backtests="recentBacktests"
        :selected-history-id="selectedHistoryId"
        :selected-history-result="selectedHistoryResult"
        @chart-ready="setHistoryChartRefs"
        @load-record="loadBacktestRecord"
        @refresh="refreshBacktests"
      />

      <JobHistoryView
        v-if="activeView === 'jobs'"
        :error="jobError"
        :jobs="recentJobs"
        :message="jobMessage"
        @cancel-job="cancelJob"
        @open-result="openJobResult"
        @refresh="refreshJobs"
        @retry-job="retryJob"
      />

      <BacktestView
        v-if="activeView === 'backtest'"
        :active-job="activeBacktestJob"
        :error="errorMessage"
        :form="form"
        :loading="loading"
        :message="backtestMessage"
        :result="result"
        :strategies="strategies"
        :strategy-param-fields="strategyParamFields"
        @chart-ready="setBacktestChartRefs"
        @select-strategy-id="selectStrategyById"
        @submit-backtest="submitBacktest"
        @update-form="updateBacktestForm"
      />

      <MarketWatchView
        v-if="activeView === 'market'"
        :auto-refresh="marketAutoRefresh"
        :error="marketError"
        :message="marketMessage"
        :series="marketSeries"
        :symbol="marketSymbol"
        :syncing="marketSyncing"
        :timeframe="marketTimeframe"
        @chart-ready="setLiveMarketChartRef"
        @refresh="refreshMarketSeries"
        @sync="syncMarketData"
        @toggle-auto-refresh="toggleMarketAutoRefresh"
        @update-symbol="updateMarketSymbol"
        @update-timeframe="updateMarketTimeframe"
      />

      <AiAnalysisView
        v-if="activeView === 'ai'"
        :analyses="aiAnalyses"
        :analysis="aiAnalysis"
        :backtests="recentBacktests"
        :error="aiError"
        :loading="aiLoading"
        :selected-backtest-id="aiBacktestId"
        @analyze="runAiAnalysis"
        @open-analysis="aiAnalysis = $event"
        @select-backtest="selectAiBacktest"
      />

      <StrategyManagerView
        v-if="activeView === 'strategies'"
        :draft="strategyDraft"
        :error="strategyError"
        :message="strategyMessage"
        :saving="strategySaving"
        :selected-strategy="selectedStrategy"
        :strategies="strategies"
        @copy-strategy="copyStrategy"
        @new-strategy="newStrategy"
        @remove-strategy="removeSelectedStrategy"
        @save-strategy="saveStrategy"
        @select-strategy="selectStrategy"
        @update-draft="updateStrategyDraft"
      />
    </section>
  </main>
</template>

<script setup>
import { BarChart, CandlestickChart, LineChart } from "echarts/charts";
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkPointComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import {
  analyzeBacktest,
  cancelBacktestJob,
  clearStoredToken,
  createBacktestJob,
  createStrategy,
  deleteStrategy,
  getBacktest,
  getBacktestJob,
  getCurrentUser,
  getMarketKlines,
  getStoredToken,
  listBacktestAnalyses,
  listBacktestJobs,
  listBacktests,
  listStrategies,
  loginUser,
  registerUser,
  retryBacktestJob,
  setStoredToken,
  syncMarketKlines,
  updateStrategy,
} from "./api";
import AccountView from "./components/AccountView.vue";
import AiAnalysisView from "./components/AiAnalysisView.vue";
import BacktestView from "./components/BacktestView.vue";
import DashboardView from "./components/DashboardView.vue";
import HistoryView from "./components/HistoryView.vue";
import JobHistoryView from "./components/JobHistoryView.vue";
import MarketWatchView from "./components/MarketWatchView.vue";
import StrategyManagerView from "./components/StrategyManagerView.vue";
import { buildEquityChartOption, buildMarketChartOption } from "./utils/chartOptions";
import { formatMoney, formatParamLabel, getParamMin } from "./utils/formatters";

echarts.use([
  BarChart,
  CandlestickChart,
  CanvasRenderer,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  LineChart,
  MarkPointComponent,
  TooltipComponent,
]);

const navItems = [
  { key: "dashboard", label: "Dashboard", title: "系统总览", eyebrow: "Overview", icon: "□" },
  { key: "backtest", label: "回测中心", title: "回测中心", eyebrow: "Backtest", icon: "◧" },
  { key: "history", label: "回测历史", title: "回测历史", eyebrow: "History", icon: "≋" },
  { key: "jobs", label: "任务中心", title: "任务中心", eyebrow: "Jobs", icon: "◇" },
  { key: "market", label: "实时行情", title: "实时行情观察", eyebrow: "Market Data", icon: "⌁" },
  { key: "ai", label: "AI 分析", title: "AI 策略分析", eyebrow: "AI Analyst", icon: "✦" },
  { key: "strategies", label: "策略管理", title: "策略管理", eyebrow: "Strategy CRUD", icon: "⌘" },
  { key: "account", label: "账户", title: "账户", eyebrow: "Auth", icon: "◎" },
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

const activeView = ref("market");
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
const marketChartRef = ref(null);
const backtestChartRef = ref(null);
const historyMarketChartRef = ref(null);
const historyChartRef = ref(null);
const liveMarketChartRef = ref(null);
const loading = ref(false);
const errorMessage = ref("");
const backtestMessage = ref("");
const activeBacktestJob = ref(null);
const result = ref(null);
const recentBacktests = ref([]);
const recentJobs = ref([]);
const jobMessage = ref("");
const jobError = ref("");
const selectedHistoryId = ref("");
const selectedHistoryResult = ref(null);
const strategies = ref([]);
const selectedStrategy = ref(null);
const strategySaving = ref(false);
const strategyMessage = ref("");
const strategyError = ref("");
const marketSymbol = ref("BTCUSDT");
const marketTimeframe = ref("1m");
const marketSeries = ref(null);
const marketSyncing = ref(false);
const marketAutoRefresh = ref(false);
const marketMessage = ref("");
const marketError = ref("");
const aiBacktestId = ref("");
const aiAnalysis = ref(null);
const aiAnalyses = ref([]);
const aiLoading = ref(false);
const aiError = ref("");
const currentUser = ref(null);
const authToken = ref(getStoredToken());
const authMode = ref("login");
const authLoading = ref(false);
const authMessage = ref("");
const authError = ref("");
let dashboardChart = null;
let marketChart = null;
let backtestChart = null;
let historyMarketChart = null;
let historyChart = null;
let liveMarketChart = null;
let backtestJobPollTimer = null;
let marketPollTimer = null;

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

const authForm = reactive({
  username: "",
  password: "",
});

onMounted(async () => {
  await initializeApp();
  window.addEventListener("resize", resizeCharts);
});

onBeforeUnmount(() => {
  stopBacktestJobPolling();
  stopMarketPolling();
  window.removeEventListener("resize", resizeCharts);
  dashboardChart?.dispose();
  marketChart?.dispose();
  backtestChart?.dispose();
  historyMarketChart?.dispose();
  historyChart?.dispose();
  liveMarketChart?.dispose();
});

watch(activeView, async () => {
  if (activeView.value === "market") {
    if (!marketAutoRefresh.value) toggleMarketAutoRefresh(true);
  } else if (marketAutoRefresh.value) {
    marketAutoRefresh.value = false;
    stopMarketPolling();
  }
  if (activeView.value === "ai" && aiBacktestId.value) await refreshAiAnalyses();
  await nextTick();
  ensureCharts();
  renderCharts();
});

async function initializeApp() {
  try {
    currentUser.value = await getCurrentUser();
    await refreshStrategies();
    await refreshJobs();
    await refreshBacktests();
    if (recentBacktests.value.length > 0) {
      result.value = await getBacktest(recentBacktests.value[0].id);
      selectedHistoryId.value = result.value.backtest_id;
      selectedHistoryResult.value = result.value;
    }
    activeView.value = "market";
    toggleMarketAutoRefresh(true);
  } catch (error) {
    authError.value = error.message;
    activeView.value = "account";
  }
}

function toggleAuthMode() {
  authMode.value = authMode.value === "login" ? "register" : "login";
  authMessage.value = "";
  authError.value = "";
}

function updateAuthForm(nextForm) {
  authForm.username = nextForm.username;
  authForm.password = nextForm.password;
}

async function submitAuth() {
  authLoading.value = true;
  authMessage.value = "";
  authError.value = "";

  try {
    if (authMode.value === "register") {
      await registerUser({
        username: authForm.username,
        password: authForm.password,
      });
      authMode.value = "login";
      authMessage.value = "注册成功，请登录";
      return;
    }

    const loginResult = await loginUser({
      username: authForm.username,
      password: authForm.password,
    });
    setStoredToken(loginResult.access_token);
    authToken.value = loginResult.access_token;
    currentUser.value = loginResult.user;
    authForm.password = "";
    authMessage.value = "登录成功";
    await refreshStrategies();
    await refreshJobs();
    await refreshBacktests();
    activeView.value = "market";
    toggleMarketAutoRefresh(true);
  } catch (error) {
    authError.value = error.message;
  } finally {
    authLoading.value = false;
  }
}

async function logout() {
  stopBacktestJobPolling();
  stopMarketPolling();
  clearStoredToken();
  authToken.value = "";
  currentUser.value = null;
  result.value = null;
  recentBacktests.value = [];
  recentJobs.value = [];
  jobMessage.value = "";
  jobError.value = "";
  selectedHistoryId.value = "";
  selectedHistoryResult.value = null;
  activeBacktestJob.value = null;
  strategies.value = [];
  selectedStrategy.value = null;
  marketSeries.value = null;
  marketAutoRefresh.value = false;
  aiAnalysis.value = null;
  aiAnalyses.value = [];
  activeView.value = "account";
  authMessage.value = "已退出";
  authError.value = "";
}

async function refreshStrategies() {
  strategies.value = await listStrategies();
  if (!selectedStrategy.value && strategies.value.length > 0) {
    selectStrategy(strategies.value[0]);
  }
}

async function submitBacktest() {
  errorMessage.value = "";
  backtestMessage.value = "";
  loading.value = true;
  stopBacktestJobPolling();

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

    activeBacktestJob.value = await createBacktestJob(payload);
    backtestMessage.value = `任务已创建：${activeBacktestJob.value.id} · ${formatJobStatus(activeBacktestJob.value.status)}`;
    await refreshJobs();
    startBacktestJobPolling(activeBacktestJob.value.id, strategy);
  } catch (error) {
    errorMessage.value = error.message;
    loading.value = false;
  }
}

function startBacktestJobPolling(jobId, strategy) {
  backtestJobPollTimer = window.setInterval(async () => {
    await pollBacktestJob(jobId, strategy);
  }, 800);
  pollBacktestJob(jobId, strategy);
}

async function pollBacktestJob(jobId, strategy) {
  try {
    const job = await getBacktestJob(jobId);
    activeBacktestJob.value = job;
    backtestMessage.value = `任务 ${job.id} · ${formatJobStatus(job.status)}`;

    if (job.status === "succeeded") {
      stopBacktestJobPolling();
      if (!job.result_backtest_id) {
        throw new Error("Backtest job succeeded without a result id");
      }
      result.value = await getBacktest(job.result_backtest_id);
      backtestMessage.value = `回测完成：${result.value.backtest_id} · ${strategy?.name ?? result.value.strategy} · ${result.value.metrics.trade_count} 笔交易 · 最终权益 ${formatMoney(result.value.metrics.final_equity)}`;
      selectedHistoryId.value = result.value.backtest_id;
      selectedHistoryResult.value = result.value;
      await refreshBacktests();
      await refreshJobs();
      await nextTick();
      ensureCharts();
      renderCharts();
      loading.value = false;
      return;
    }

    if (job.status === "failed" || job.status === "cancelled") {
      stopBacktestJobPolling();
      errorMessage.value = job.error_message || `Backtest job ${job.status}`;
      await refreshJobs();
      loading.value = false;
    }
  } catch (error) {
    stopBacktestJobPolling();
    errorMessage.value = error.message;
    loading.value = false;
  }
}

function stopBacktestJobPolling() {
  if (backtestJobPollTimer) {
    window.clearInterval(backtestJobPollTimer);
    backtestJobPollTimer = null;
  }
}

function formatJobStatus(status) {
  const labels = {
    queued: "排队中",
    running: "运行中",
    succeeded: "已完成",
    failed: "失败",
    cancelled: "已取消",
  };
  return labels[status] ?? status;
}

async function refreshBacktests() {
  recentBacktests.value = await listBacktests(20);
  if (!aiBacktestId.value && recentBacktests.value.length > 0) {
    aiBacktestId.value = recentBacktests.value[0].id;
  }
}

async function refreshMarketSeries() {
  marketError.value = "";
  try {
    marketSeries.value = await getMarketKlines(
      marketSymbol.value,
      marketTimeframe.value,
      2000,
      "today_shanghai",
    );
    await nextTick();
    ensureCharts();
    renderCharts();
  } catch (error) {
    marketError.value = error.message;
  }
}

async function syncMarketData() {
  if (marketSyncing.value) return;
  marketSyncing.value = true;
  marketMessage.value = "";
  marketError.value = "";
  try {
    const syncResult = await syncMarketKlines({
      symbol: marketSymbol.value,
      timeframe: marketTimeframe.value,
      limit: 2000,
      range: "today_shanghai",
    });
    marketMessage.value = `同步完成：新增 ${syncResult.inserted}，更新 ${syncResult.updated}`;
    await refreshMarketSeries();
  } catch (error) {
    marketError.value = error.message;
  } finally {
    marketSyncing.value = false;
  }
}

function updateMarketSymbol(value) {
  marketSymbol.value = value;
  refreshMarketSeries();
}

function updateMarketTimeframe(value) {
  marketTimeframe.value = value;
  refreshMarketSeries();
}

function toggleMarketAutoRefresh(enabled) {
  marketAutoRefresh.value = enabled;
  stopMarketPolling();
  if (enabled) {
    syncMarketData();
    marketPollTimer = window.setInterval(syncMarketData, 10000);
  }
}

function stopMarketPolling() {
  if (marketPollTimer) {
    window.clearInterval(marketPollTimer);
    marketPollTimer = null;
  }
}

async function selectAiBacktest(id) {
  aiBacktestId.value = id;
  aiAnalysis.value = null;
  await refreshAiAnalyses();
}

async function refreshAiAnalyses() {
  if (!aiBacktestId.value) {
    aiAnalyses.value = [];
    return;
  }
  aiError.value = "";
  try {
    aiAnalyses.value = await listBacktestAnalyses(aiBacktestId.value);
    if (!aiAnalysis.value && aiAnalyses.value.length > 0) {
      aiAnalysis.value = aiAnalyses.value[0];
    }
  } catch (error) {
    aiError.value = error.message;
  }
}

async function runAiAnalysis() {
  if (!aiBacktestId.value) return;
  aiLoading.value = true;
  aiError.value = "";
  try {
    aiAnalysis.value = await analyzeBacktest(aiBacktestId.value);
    await refreshAiAnalyses();
  } catch (error) {
    aiError.value = error.message;
  } finally {
    aiLoading.value = false;
  }
}

async function refreshJobs() {
  recentJobs.value = await listBacktestJobs(30);
}

async function cancelJob(jobId) {
  jobError.value = "";
  jobMessage.value = "";
  try {
    const job = await cancelBacktestJob(jobId);
    jobMessage.value = `任务 ${job.id} 已请求取消`;
    if (activeBacktestJob.value?.id === job.id) {
      activeBacktestJob.value = job;
      if (job.status === "cancelled") {
        stopBacktestJobPolling();
        loading.value = false;
      }
    }
    await refreshJobs();
  } catch (error) {
    jobError.value = error.message;
  }
}

async function retryJob(jobId) {
  jobError.value = "";
  jobMessage.value = "";
  try {
    const job = await retryBacktestJob(jobId);
    jobMessage.value = `已创建重试任务：${job.id}`;
    await refreshJobs();
  } catch (error) {
    jobError.value = error.message;
  }
}

async function openJobResult(backtestId) {
  await loadBacktestRecord(backtestId);
  activeView.value = "history";
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

function selectStrategyById(strategyId) {
  const strategy = strategies.value.find((item) => item.id === strategyId);
  if (strategy) selectStrategy(strategy);
}

function updateBacktestForm(nextForm) {
  form.symbol = nextForm.symbol;
  form.strategyId = nextForm.strategyId;
  form.timeframe = nextForm.timeframe;
  form.startDate = nextForm.startDate;
  form.endDate = nextForm.endDate;
  form.initialCash = nextForm.initialCash;
  form.params = { ...nextForm.params };
}

function updateStrategyDraft(nextDraft) {
  strategyDraft.name = nextDraft.name;
  strategyDraft.description = nextDraft.description;
  strategyDraft.status = nextDraft.status;
  strategyDraft.code = nextDraft.code;
  strategyDraft.paramsText = nextDraft.paramsText;
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
  if (marketChartRef.value && !marketChart) {
    marketChart = echarts.init(marketChartRef.value);
  }
  if (backtestChartRef.value && !backtestChart) {
    backtestChart = echarts.init(backtestChartRef.value);
  }
  if (historyMarketChartRef.value && !historyMarketChart) {
    historyMarketChart = echarts.init(historyMarketChartRef.value);
  }
  if (historyChartRef.value && !historyChart) {
    historyChart = echarts.init(historyChartRef.value);
  }
  if (liveMarketChartRef.value && !liveMarketChart) {
    liveMarketChart = echarts.init(liveMarketChartRef.value);
  }
}

function setDashboardChartRef(element) {
  if (dashboardChartRef.value !== element) {
    dashboardChart?.dispose();
    dashboardChart = null;
    dashboardChartRef.value = element;
  }
  ensureCharts();
  renderCharts();
}

function setBacktestChartRefs(elements) {
  if (marketChartRef.value !== elements.market) {
    marketChart?.dispose();
    marketChart = null;
    marketChartRef.value = elements.market;
  }
  if (backtestChartRef.value !== elements.equity) {
    backtestChart?.dispose();
    backtestChart = null;
    backtestChartRef.value = elements.equity;
  }
  ensureCharts();
  renderCharts();
}

function setHistoryChartRefs(elements) {
  if (historyMarketChartRef.value !== elements.market) {
    historyMarketChart?.dispose();
    historyMarketChart = null;
    historyMarketChartRef.value = elements.market;
  }
  if (historyChartRef.value !== elements.equity) {
    historyChart?.dispose();
    historyChart = null;
    historyChartRef.value = elements.equity;
  }
  ensureCharts();
  renderCharts();
}

function setLiveMarketChartRef(element) {
  if (liveMarketChartRef.value !== element) {
    liveMarketChart?.dispose();
    liveMarketChart = null;
    liveMarketChartRef.value = element;
  }
  ensureCharts();
  renderCharts();
}

function renderCharts() {
  renderChart(dashboardChart, result.value);
  renderMarketChart(marketChart, result.value);
  renderChart(backtestChart, result.value);
  renderMarketChart(historyMarketChart, selectedHistoryResult.value);
  renderChart(historyChart, selectedHistoryResult.value);
  renderMarketChart(liveMarketChart, liveMarketChartSource());
}

function liveMarketChartSource() {
  if (!marketSeries.value) return null;
  return {
    market_klines: marketSeries.value.klines.map((item) => ({
      ...item,
      date: formatShanghaiChartTime(item.open_time),
    })),
    trades: [],
  };
}

function formatShanghaiChartTime(value) {
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function renderChart(chart, source) {
  if (!chart || !source) return;
  chart.setOption(buildEquityChartOption(source));
}

function renderMarketChart(chart, source) {
  if (!chart || !source || !source.market_klines?.length) return;
  chart.setOption(buildMarketChartOption(source));
}

function resizeCharts() {
  dashboardChart?.resize();
  marketChart?.resize();
  backtestChart?.resize();
  historyMarketChart?.resize();
  historyChart?.resize();
  liveMarketChart?.resize();
}

function getStrategyKind(strategy) {
  if (strategy?.strategy_type === "custom_code") return "custom_code";
  if (strategy?.id === "rsi-reversal-default") return "rsi_reversal";
  return "ma_cross";
}
</script>
