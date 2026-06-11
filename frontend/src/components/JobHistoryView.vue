<template>
  <section class="content-card">
    <div class="section-heading">
      <h2>任务中心</h2>
      <button class="secondary-button" type="button" @click="$emit('refresh')">刷新</button>
    </div>

    <p v-if="message" class="success-message">{{ message }}</p>
    <p v-if="error" class="error-message">{{ error }}</p>

    <div class="table-wrap job-table">
      <table>
        <thead>
          <tr>
            <th>创建时间</th>
            <th>任务</th>
            <th>状态</th>
            <th>标的</th>
            <th>区间</th>
            <th>尝试</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="job in jobs" :key="job.id">
            <td>{{ formatDateTime(job.created_at) }}</td>
            <td>
              <span class="mono-id">{{ job.id }}</span>
              <small v-if="job.retry_of_job_id">重试 {{ job.retry_of_job_id }}</small>
            </td>
            <td>
              <span :class="['job-badge', job.status]">{{ formatJobStatus(job.status) }}</span>
            </td>
            <td>{{ job.request_payload.symbol }} · {{ job.request_payload.timeframe }}</td>
            <td>{{ job.request_payload.start_date }} 至 {{ job.request_payload.end_date }}</td>
            <td>{{ job.attempt }}</td>
            <td>
              <div class="row-actions">
                <button
                  v-if="job.result_backtest_id"
                  class="link-button"
                  type="button"
                  @click="$emit('open-result', job.result_backtest_id)"
                >
                  结果
                </button>
                <button
                  v-if="canCancel(job)"
                  class="link-button"
                  type="button"
                  @click="$emit('cancel-job', job.id)"
                >
                  取消
                </button>
                <button
                  v-if="canRetry(job)"
                  class="link-button"
                  type="button"
                  @click="$emit('retry-job', job.id)"
                >
                  重试
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { formatDateTime } from "../utils/formatters";

defineProps({
  error: {
    type: String,
    default: "",
  },
  jobs: {
    type: Array,
    required: true,
  },
  message: {
    type: String,
    default: "",
  },
});

defineEmits(["cancel-job", "open-result", "refresh", "retry-job"]);

function canCancel(job) {
  return job.status === "queued" || job.status === "running";
}

function canRetry(job) {
  return job.status === "failed" || job.status === "cancelled";
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
