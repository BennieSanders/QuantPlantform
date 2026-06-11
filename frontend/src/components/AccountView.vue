<template>
  <section class="account-layout">
    <section class="content-card">
      <div class="section-heading">
        <h2>当前账户</h2>
        <span>{{ authToken ? "Token 已保存" : "开发默认用户" }}</span>
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

    <section class="content-card auth-card">
      <div class="section-heading">
        <h2>{{ mode === "login" ? "登录" : "注册" }}</h2>
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
