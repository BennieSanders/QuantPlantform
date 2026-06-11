<template>
  <section class="view-stack">
    <section class="content-card ai-toolbar">
      <div class="form-row">
        <label class="wide-field">
          分析回测
          <select :value="selectedBacktestId" @change="$emit('select-backtest', $event.target.value)">
            <option value="">请选择回测记录</option>
            <option v-for="record in backtests" :key="record.id" :value="record.id">
              {{ record.symbol }} · {{ record.strategy_name }} · {{ record.created_at }}
            </option>
          </select>
        </label>
        <button :disabled="loading || !selectedBacktestId" type="button" @click="$emit('analyze')">
          {{ loading ? "分析中..." : "生成 AI 分析" }}
        </button>
      </div>
      <p class="field-hint">当前使用可离线复现的量化分析提供器，输出会保存到数据库。</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </section>

    <section v-if="analysis" class="content-card ai-report">
      <div class="section-heading">
        <h2>分析结论</h2>
        <span :class="['risk-badge', `risk-${analysis.risk_level}`]">
          风险 {{ riskLabel(analysis.risk_level) }}
        </span>
      </div>
      <p class="ai-summary">{{ analysis.summary }}</p>

      <div class="ai-grid">
        <article>
          <h3>优势</h3>
          <ul><li v-for="item in analysis.strengths" :key="item">{{ item }}</li></ul>
        </article>
        <article>
          <h3>风险提示</h3>
          <ul><li v-for="item in analysis.warnings" :key="item">{{ item }}</li></ul>
        </article>
        <article>
          <h3>行动建议</h3>
          <ul><li v-for="item in analysis.recommendations" :key="item">{{ item }}</li></ul>
        </article>
        <article>
          <h3>建议参数</h3>
          <dl class="param-list">
            <template v-for="(value, key) in analysis.suggested_params" :key="key">
              <dt>{{ key }}</dt><dd>{{ value }}</dd>
            </template>
          </dl>
        </article>
      </div>
    </section>

    <section class="content-card">
      <div class="section-heading"><h2>历史分析</h2><span>{{ analyses.length }} 条</span></div>
      <div class="analysis-history">
        <button
          v-for="item in analyses"
          :key="item.id"
          class="analysis-history-item"
          type="button"
          @click="$emit('open-analysis', item)"
        >
          <strong>{{ riskLabel(item.risk_level) }}风险 · {{ item.provider }}</strong>
          <span>{{ item.created_at }}</span>
        </button>
      </div>
    </section>
  </section>
</template>

<script setup>
defineProps({
  analyses: { type: Array, required: true },
  analysis: { type: Object, default: null },
  backtests: { type: Array, required: true },
  error: { type: String, default: "" },
  loading: { type: Boolean, default: false },
  selectedBacktestId: { type: String, default: "" },
});

defineEmits(["analyze", "open-analysis", "select-backtest"]);

function riskLabel(level) {
  return { low: "低", medium: "中", high: "高" }[level] ?? level;
}
</script>
