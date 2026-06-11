<template>
  <section class="workspace">
    <aside class="control-panel">
      <form class="form-grid" @submit.prevent="$emit('submit-backtest')">
        <label>
          交易标的
          <select :value="form.symbol" @change="updateForm('symbol', $event.target.value)">
            <option value="BTCUSDT">BTCUSDT</option>
            <option value="ETHUSDT">ETHUSDT</option>
          </select>
        </label>

        <label>
          策略
          <select :value="form.strategyId" @change="$emit('select-strategy-id', $event.target.value)">
            <option v-for="strategy in strategies" :key="strategy.id" :value="strategy.id">
              {{ strategy.name }}
            </option>
          </select>
        </label>

        <label>
          K 线周期
          <select :value="form.timeframe" @change="updateForm('timeframe', $event.target.value)">
            <option value="1d">日线</option>
            <option value="1h">1 小时</option>
          </select>
        </label>

        <label>
          开始日期
          <input :value="form.startDate" type="date" @input="updateForm('startDate', $event.target.value)" />
        </label>

        <label>
          结束日期
          <input :value="form.endDate" type="date" @input="updateForm('endDate', $event.target.value)" />
        </label>

        <p class="field-hint">示例 CSV 默认覆盖 2024 年日线；回填后可切换到 1h 数据。</p>

        <label>
          初始资金
          <input
            :value="form.initialCash"
            min="100"
            step="100"
            type="number"
            @input="updateForm('initialCash', Number($event.target.value))"
          />
        </label>

        <label v-for="field in strategyParamFields" :key="field.key">
          {{ field.label }}
          <input
            :min="field.min"
            :step="field.step"
            :value="form.params[field.key]"
            type="number"
            @input="updateParam(field.key, Number($event.target.value))"
          />
        </label>

        <button :disabled="loading" type="submit">
          {{ loading ? "任务执行中..." : "运行回测" }}
        </button>
      </form>

      <div v-if="activeJob" class="job-status">
        <span>任务状态</span>
        <strong>{{ formatJobStatus(activeJob.status) }}</strong>
        <small>{{ activeJob.id }}</small>
      </div>

      <p v-if="message" class="success-message">{{ message }}</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </aside>

    <section class="result-panel">
      <div class="content-card chart-card">
        <div class="section-heading">
          <h2>行情图</h2>
          <span>{{ result?.symbol ?? "BTCUSDT" }} · {{ result?.timeframe ?? "1d" }}</span>
        </div>
        <div ref="marketChartRef" class="chart chart-market"></div>
      </div>

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

      <div ref="equityChartRef" class="chart chart-equity"></div>
      <TradeTable :trades="result?.trades ?? []" />
    </section>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import TradeTable from "./TradeTable.vue";
import { formatMoney, formatNumber, formatPercent } from "../utils/formatters";

const props = defineProps({
  activeJob: {
    type: Object,
    default: null,
  },
  error: {
    type: String,
    default: "",
  },
  form: {
    type: Object,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  message: {
    type: String,
    default: "",
  },
  result: {
    type: Object,
    default: null,
  },
  strategies: {
    type: Array,
    required: true,
  },
  strategyParamFields: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(["chart-ready", "select-strategy-id", "submit-backtest", "update-form"]);
const marketChartRef = ref(null);
const equityChartRef = ref(null);

onMounted(() => {
  emit("chart-ready", {
    market: marketChartRef.value,
    equity: equityChartRef.value,
  });
});

function updateForm(field, value) {
  emit("update-form", { ...props.form, [field]: value });
}

function updateParam(key, value) {
  emit("update-form", {
    ...props.form,
    params: {
      ...props.form.params,
      [key]: value,
    },
  });
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
</script>
