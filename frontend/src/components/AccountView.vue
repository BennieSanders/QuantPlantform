<template>
  <section :class="standalone ? 'auth-gateway' : 'account-layout'">
    <div v-if="standalone" class="auth-ornament auth-ornament-one"></div>
    <div v-if="standalone" class="auth-ornament auth-ornament-two"></div>
    <div v-if="standalone" class="auth-backdrop"></div>
    <section v-if="standalone" class="auth-intro">
      <span class="auth-logo">Q</span>
      <p class="eyebrow">Quant Research Platform</p>
      <h1>量化研究，从可信数据开始</h1>
      <p class="auth-lead">实时行情、策略回测、风险指标与 AI 分析集中在一个研究工作台。</p>
      <div class="auth-chips" aria-label="平台能力">
        <span>实时 K 线</span>
        <span>回测中心</span>
        <span>AI 分析</span>
      </div>
      <div class="auth-highlights">
        <article>
          <strong>实时</strong>
          <span>行情接入与多周期观察</span>
        </article>
        <article>
          <strong>工程化</strong>
          <span>策略、任务、历史数据闭环</span>
        </article>
        <article>
          <strong>智能化</strong>
          <span>AI 风险解读与参数建议</span>
        </article>
      </div>
    </section>

    <section v-if="currentUser" class="content-card">
      <div class="section-heading">
        <h2>当前账户</h2>
        <span>{{ authToken ? "已认证" : "未认证" }}</span>
      </div>

      <div class="account-summary">
        <article class="metric">
          <span>用户名</span>
          <strong>{{ currentUser?.username ?? "-" }}</strong>
        </article>
        <article class="metric">
          <span>用户 ID</span>
          <strong>{{ currentUser?.id ?? "-" }}</strong>
        </article>
        <article class="metric">
          <span>状态</span>
          <strong>{{ currentUser?.status ?? "-" }}</strong>
        </article>
      </div>
    </section>

    <section v-if="!currentUser" :class="['content-card', 'auth-card', { 'auth-card-standalone': standalone }]">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{{ mode === "login" ? "Welcome Back" : "Create Account" }}</p>
          <h2>{{ mode === "login" ? "登录平台" : "注册账户" }}</h2>
        </div>
        <button class="secondary-button" type="button" @click="$emit('toggle-mode')">
          {{ mode === "login" ? "切换注册" : "切换登录" }}
        </button>
      </div>

      <form class="form-grid" @submit.prevent="$emit('submit-auth')">
        <label>
          用户名
          <input
            :value="form.username"
            autocomplete="username"
            @input="updateField('username', $event.target.value)"
          />
        </label>
        <label>
          密码
          <input
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            :value="form.password"
            type="password"
            @input="updateField('password', $event.target.value)"
          />
        </label>
        <button :disabled="loading" type="submit">
          {{ loading ? "处理中..." : mode === "login" ? "登录" : "注册" }}
        </button>
      </form>

      <p class="auth-note">登录后才能访问行情、回测、策略和 AI 分析功能。</p>

      <p v-if="message" class="success-message">{{ message }}</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </section>
  </section>
</template>

<script setup>
const props = defineProps({
  authToken: {
    type: String,
    default: "",
  },
  standalone: {
    type: Boolean,
    default: false,
  },
  currentUser: {
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
  mode: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["submit-auth", "toggle-mode", "update-form"]);

function updateField(field, value) {
  emit("update-form", { ...props.form, [field]: value });
}
</script>
