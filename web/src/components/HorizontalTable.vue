<script setup lang="ts">
withDefaults(defineProps<{ minWidth?: string }>(), { minWidth: '720px' })
</script>

<template>
  <div class="horizontal-table-shell" :style="{ '--table-min-width': minWidth }">
    <div class="horizontal-scroll-hint"><van-icon name="exchange" /><span>左右滑动查看更多</span></div>
    <div class="horizontal-scroll-region"><slot /></div>
  </div>
</template>

<style scoped>
.horizontal-table-shell { width: 100%; min-width: 0; overflow: hidden; background: #fff; border-radius: 8px; }
.horizontal-scroll-hint { display: none; align-items: center; justify-content: flex-end; gap: 4px; padding: 7px 10px 5px; color: #969799; font-size: 11px; border-bottom: 1px solid #f2f3f5; }
.horizontal-scroll-region { width: 100%; max-width: 100%; overflow-x: auto; overflow-y: hidden; -webkit-overflow-scrolling: touch; overscroll-behavior-x: contain; touch-action: pan-x pan-y; scrollbar-width: thin; scrollbar-color: #c8c9cc transparent; }
.horizontal-scroll-region::-webkit-scrollbar { height: 6px; }
.horizontal-scroll-region::-webkit-scrollbar-thumb { background: #c8c9cc; border-radius: 999px; }
.horizontal-scroll-region :deep(table) { width: 100%; min-width: var(--table-min-width); }
@media (max-width: 767px) { .horizontal-scroll-hint { display: flex; } }
</style>
