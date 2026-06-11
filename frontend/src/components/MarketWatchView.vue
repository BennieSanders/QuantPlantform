<template>
  <section class="view-stack">
    <section class="content-card market-toolbar">
      <div class="form-row">
        <label>
          交易标的
          <select :value="symbol" @change="$emit('update-symbol', $event.target.value)">
            <option value="BTCUSDT">BTCUSDT</option>
            <option value="ETHUSDT">ETHUSDT</option>
          </select>
        </label>
        <label>
          周期
          <select :value="timeframe" @change="$emit('update-timeframe', $event.target.value)">
            <option value="1m">1 分钟</option>
            <option value="5m">5 分钟</option>
            <option value="15m">15 分钟</option>
            <option value="1h">1 小时</option>
            <option value="1d">日线</option>
          </select>
        </label>
        <button class="secondary-button" type="button" @click="$emit('refresh')">读取数据库</button>
        <button :disabled="syncing" type="button" @click="$emit('sync')">
          {{ syncing ? "同步中..." : "拉取并入库" }}
        </button>
        <label class="inline-toggle">
          <input
            :checked="autoRefresh"
            type="checkbox"
            @change="$emit('toggle-auto-refresh', $event.target.checked)"
          />
          自动观察
        </label>
      </div>
      <p class="field-hint">加密货币 24 小时交易。这里以北京时间 00:00 为当日开盘，展示从今日开始到现在的 K 线，并每 10 秒更新。</p>
      <p v-if="message" class="success-message">{{ message }}</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </section>

    <div class="summary-grid">
      <article class="metric">
        <span>最新价格</span>
        <strong>{{ formatMoney(series?.last_price) }}</strong>
      </article>
      <article class="metric">
        <span>今日涨跌</span>
        <strong>{{ formatPercent(series?.change_rate) }}</strong>
      </article>
      <article class="metric">
        <span>今日 K 线</span>
        <strong>{{ series?.count ?? 0 }}</strong>
      </article>
      <article class="metric">
        <span>最后入库</span>
        <strong class="metric-time">{{ formatDateTime(series?.last_ingested_at) }}</strong>
      </article>
    </div>

    <section class="content-card chart-card">
      <div class="section-heading">
        <h2>实时行情观察</h2>
        <span>{{ symbol }} · {{ timeframe }}</span>
      </div>
      <div ref="chartRef" class="chart chart-market"></div>
    </section>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { formatDateTime, formatMoney, formatPercent } from "../utils/formatters";

defineProps({
  autoRefresh: { type: Boolean, default: false },
  error: { type: String, default: "" },
  message: { type: String, default: "" },
  series: { type: Object, default: null },
  symbol: { type: String, required: true },
  syncing: { type: Boolean, default: false },
  timeframe: { type: String, required: true },
});

const emit = defineEmits([
  "chart-ready",
  "refresh",
  "sync",
  "toggle-auto-refresh",
  "update-symbol",
  "update-timeframe",
]);
const chartRef = ref(null);

onMounted(() => emit("chart-ready", chartRef.value));
</script>
