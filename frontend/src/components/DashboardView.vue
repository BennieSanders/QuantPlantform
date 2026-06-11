<template>
  <section class="view-stack">
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
        <h2>历史回测 K 线（非实时）</h2>
        <span>{{ result?.symbol ?? "BTCUSDT" }} · {{ result?.timeframe ?? "1d" }}</span>
      </div>
      <div ref="chartRef" class="chart chart-market"></div>
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
</template>

<script setup>
import { onMounted, ref } from "vue";
import { formatDateTime, formatMoney, formatNumber, formatPercent } from "../utils/formatters";

defineProps({
  recentBacktests: {
    type: Array,
    required: true,
  },
  result: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["chart-ready"]);
const chartRef = ref(null);

onMounted(() => {
  emit("chart-ready", chartRef.value);
});
</script>
