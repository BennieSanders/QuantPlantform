<template>
  <section class="history-layout">
    <section class="content-card">
      <div class="section-heading">
        <h2>回测历史</h2>
        <button class="secondary-button" type="button" @click="$emit('refresh')">刷新</button>
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
              @click="$emit('load-record', record.id)"
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

      <div ref="marketChartRef" class="chart chart-market"></div>
      <div ref="equityChartRef" class="chart chart-equity"></div>
      <TradeTable :trades="selectedHistoryResult?.trades ?? []" />
    </section>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import TradeTable from "./TradeTable.vue";
import { formatDateTime, formatNumber, formatPercent } from "../utils/formatters";

defineProps({
  recentBacktests: {
    type: Array,
    required: true,
  },
  selectedHistoryId: {
    type: String,
    default: "",
  },
  selectedHistoryResult: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["chart-ready", "load-record", "refresh"]);
const marketChartRef = ref(null);
const equityChartRef = ref(null);

onMounted(() => {
  emit("chart-ready", {
    market: marketChartRef.value,
    equity: equityChartRef.value,
  });
});
</script>
