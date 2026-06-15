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
      <p class="field-hint">按周期自动加载合理观察窗口：1 分钟看 1 天、5 分钟看 3 天、15 分钟看 7 天、1 小时看 30 天、日线看 1 年。</p>
      <p v-if="message" class="success-message">{{ message }}</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </section>

    <div class="summary-grid">
      <article class="metric">
        <span>最新价格</span>
        <strong>{{ formatMoney(series?.last_price) }}</strong>
      </article>
      <article class="metric">
        <span>窗口涨跌</span>
        <strong>{{ formatPercent(series?.change_rate) }}</strong>
      </article>
      <article class="metric">
        <span>窗口 K 线</span>
        <strong>{{ series?.count ?? 0 }}</strong>
      </article>
      <article class="metric">
        <span>最后入库</span>
        <strong class="metric-time">{{ formatDateTime(series?.last_ingested_at) }}</strong>
      </article>
      <article class="metric">
        <span>数据状态</span>
        <strong :class="['metric-status', `metric-status-${series?.health?.status ?? 'empty'}`]">
          {{ formatHealthStatus(series?.health?.status) }}
        </strong>
      </article>
    </div>

    <p v-if="series?.health" class="field-hint market-health-hint">
      预期周期 {{ formatDuration(series.health.expected_bar_seconds) }} ·
      断档 {{ series.health.gap_count }} 段 / 缺失 {{ series.health.missing_bars }} 根 ·
      数据年龄 {{ formatAge(series.health.age_minutes) }}
    </p>

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

function formatHealthStatus(status) {
  const labels = {
    empty: "无数据",
    fresh: "正常",
    watch: "关注",
    stale: "过期",
  };
  return labels[status] ?? status ?? "-";
}

function formatDuration(seconds) {
  if (!seconds) return "-";
  if (seconds % 86400 === 0) return `${seconds / 86400} 天`;
  if (seconds % 3600 === 0) return `${seconds / 3600} 小时`;
  if (seconds % 60 === 0) return `${seconds / 60} 分钟`;
  return `${seconds} 秒`;
}

function formatAge(minutes) {
  if (minutes === undefined || minutes === null) return "-";
  if (minutes < 60) return `${minutes.toFixed(1)} 分钟`;
  return `${(minutes / 60).toFixed(1)} 小时`;
}

onMounted(() => emit("chart-ready", chartRef.value));
</script>
