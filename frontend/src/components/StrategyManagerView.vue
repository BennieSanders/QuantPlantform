<template>
  <section class="strategy-layout">
    <section class="content-card strategy-list">
      <div class="section-heading">
        <h2>策略列表</h2>
        <button class="secondary-button" type="button" @click="$emit('new-strategy')">新建策略</button>
      </div>

      <button
        v-for="strategy in strategies"
        :key="strategy.id"
        :class="{ active: selectedStrategy?.id === strategy.id }"
        class="strategy-item"
        type="button"
        @click="$emit('select-strategy', strategy)"
      >
        <span>
          <strong>{{ strategy.name }}</strong>
          <button class="link-button" type="button" @click.stop="$emit('copy-strategy', strategy)">复制</button>
        </span>
        <small>{{ formatStrategyType(strategy.strategy_type) }} · {{ formatStatus(strategy.status) }}</small>
      </button>
    </section>

    <section class="content-card strategy-editor">
      <div class="section-heading">
        <h2>策略编辑</h2>
        <span>{{ selectedStrategy?.id ?? "未保存" }}</span>
      </div>

      <form class="editor-grid" @submit.prevent="$emit('save-strategy')">
        <label>
          策略名称
          <input :value="draft.name" @input="updateDraft('name', $event.target.value)" />
        </label>

        <label>
          策略说明
          <input :value="draft.description" @input="updateDraft('description', $event.target.value)" />
        </label>

        <label>
          状态
          <select :value="draft.status" @change="updateDraft('status', $event.target.value)">
            <option value="draft">草稿</option>
            <option value="active">启用</option>
            <option value="archived">归档</option>
          </select>
        </label>

        <label>
          默认参数 JSON
          <textarea
            :value="draft.paramsText"
            class="params-editor"
            @input="updateDraft('paramsText', $event.target.value)"
          ></textarea>
        </label>

        <label class="code-field">
          策略代码
          <textarea
            :value="draft.code"
            class="code-editor"
            spellcheck="false"
            @input="updateDraft('code', $event.target.value)"
          ></textarea>
        </label>

        <div class="editor-actions">
          <button :disabled="saving" type="submit">
            {{ saving ? "保存中..." : "保存策略" }}
          </button>
          <button
            v-if="selectedStrategy?.strategy_type === 'builtin'"
            class="secondary-button"
            type="button"
            @click="$emit('copy-strategy', selectedStrategy)"
          >
            复制为自定义策略
          </button>
          <button
            v-if="selectedStrategy && selectedStrategy.strategy_type !== 'builtin'"
            class="danger-button"
            type="button"
            @click="$emit('remove-strategy')"
          >
            删除策略
          </button>
        </div>
      </form>

      <p v-if="message" class="success-message">{{ message }}</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </section>
  </section>
</template>

<script setup>
import { formatStatus, formatStrategyType } from "../utils/formatters";

const props = defineProps({
  draft: {
    type: Object,
    required: true,
  },
  error: {
    type: String,
    default: "",
  },
  message: {
    type: String,
    default: "",
  },
  saving: {
    type: Boolean,
    default: false,
  },
  selectedStrategy: {
    type: Object,
    default: null,
  },
  strategies: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits([
  "copy-strategy",
  "new-strategy",
  "remove-strategy",
  "save-strategy",
  "select-strategy",
  "update-draft",
]);

function updateDraft(field, value) {
  emit("update-draft", { ...props.draft, [field]: value });
}
</script>
