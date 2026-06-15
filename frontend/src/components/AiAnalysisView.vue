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
        <label>
          分析模式
          <select :value="mode" @change="$emit('update-mode', $event.target.value)">
            <option value="gemini">Google Gemini</option>
            <option value="openai">OpenAI 大模型</option>
            <option value="local">本地引擎</option>
          </select>
        </label>
      </div>
      <p class="field-hint">当前支持 Google Gemini、OpenAI 和本地离线引擎切换，输出都会保存到数据库。</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </section>

    <section v-if="analysis" class="content-card ai-report">
      <div class="section-heading">
        <h2>分析结论</h2>
        <div class="ai-badges">
          <span class="ai-provider">{{ analysis.provider }}</span>
          <span :class="['risk-badge', `risk-${analysis.risk_level}`]">
            风险 {{ riskLabel(analysis.risk_level) }}
          </span>
        </div>
      </div>
      <p class="ai-summary">{{ analysis.summary }}</p>
      <p v-if="fallbackMessage(analysis)" class="error-message ai-fallback-message">
        {{ fallbackMessage(analysis) }}
      </p>
      <p v-if="analysis.provider.startsWith('local-')" class="field-hint">
        当前结果来自本地离线引擎。
      </p>
      <p v-else-if="analysis.provider.startsWith('gemini:')" class="field-hint">
        当前结果来自 Google Gemini 模型。
      </p>
      <p v-else class="field-hint">
        当前结果来自 OpenAI 模型。
      </p>

      <div class="summary-grid ai-score-grid">
        <article class="metric">
          <span>推荐评分</span>
          <strong>{{ analysis.score }}/100</strong>
        </article>
        <article class="metric">
          <span>模型置信度</span>
          <strong>{{ formatConfidence(analysis.confidence) }}</strong>
        </article>
        <article class="metric">
          <span>分析类型</span>
          <strong>{{ analysisTypeLabel(analysis.analysis_type) }}</strong>
        </article>
        <article class="metric">
          <span>落地阶段</span>
          <strong>{{ readinessLabel(analysis.readiness) }}</strong>
        </article>
      </div>

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
        <article>
          <h3>适配场景</h3>
          <ul><li v-for="item in analysis.fit_profile" :key="item">{{ item }}</li></ul>
        </article>
        <article>
          <h3>不建议场景</h3>
          <ul><li v-for="item in analysis.avoid_profile" :key="item">{{ item }}</li></ul>
        </article>
        <article class="ai-plan-card">
          <h3>执行计划</h3>
          <ol>
            <li v-for="item in analysis.execution_plan" :key="item">{{ item }}</li>
          </ol>
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
  mode: { type: String, default: "gemini" },
  selectedBacktestId: { type: String, default: "" },
});

defineEmits(["analyze", "open-analysis", "select-backtest", "update-mode"]);

function riskLabel(level) {
  return { low: "低", medium: "中", high: "高" }[level] ?? level;
}

function analysisTypeLabel(type) {
  return {
    trend_following: "趋势跟随",
    mean_reversion: "均值回归",
    hybrid_candidate: "混合候选",
  }[type] ?? type;
}

function readinessLabel(readiness) {
  return {
    limited_live: "可小仓位试运行",
    paper: "适合纸面验证",
    research: "仍处研究阶段",
  }[readiness] ?? readiness;
}

function formatConfidence(value) {
  if (value === undefined || value === null) return "-";
  return `${Math.round(Number(value) * 100)}%`;
}

function fallbackMessage(analysis) {
  if (!analysis?.provider?.startsWith("local-")) return "";
  return analysis.recommendations?.find(
    (item) => item.startsWith("OpenAI API") || item.startsWith("Gemini API"),
  ) ?? "";
}
</script>
