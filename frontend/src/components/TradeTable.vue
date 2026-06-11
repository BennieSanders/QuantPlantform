<template>
  <section class="table-section">
    <div class="section-heading">
      <h2>交易记录</h2>
      <span>{{ trades.length }} 条记录</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>日期</th>
            <th>方向</th>
            <th>价格</th>
            <th>数量</th>
            <th>手续费</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="trade in trades" :key="`${trade.date}-${trade.side}`">
            <td>{{ trade.date }}</td>
            <td>
              <span :class="['side', trade.side]">{{ formatSide(trade.side) }}</span>
            </td>
            <td>{{ formatMoney(trade.price) }}</td>
            <td>{{ trade.quantity.toFixed(6) }}</td>
            <td>{{ formatMoney(trade.fee) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { formatMoney, formatSide } from "../utils/formatters";

defineProps({
  trades: {
    type: Array,
    required: true,
  },
});
</script>
