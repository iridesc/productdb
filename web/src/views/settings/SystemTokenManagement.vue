<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { showConfirmDialog, showSuccessToast, showToast } from 'vant'
import { createSystemToken, deleteSystemToken, getSystemTokens, updateSystemToken } from '@/api/systemToken'
import type { SystemToken } from '@/types/systemToken'

const tokens = ref<SystemToken[]>([])
const loading = ref(false)
const showEditor = ref(false)
const editing = ref<SystemToken | null>(null)
const revealedToken = ref('')
const showRevealed = ref(false)
const form = ref({ name: '', description: '', expires_at: '' })

function formatTime(value?: string | null) {
  return value ? new Date(value).toLocaleString() : '从未'
}

async function loadTokens() {
  loading.value = true
  try {
    tokens.value = await getSystemTokens()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = { name: '', description: '', expires_at: '' }
  showEditor.value = true
}

function openEdit(token: SystemToken) {
  editing.value = token
  form.value = {
    name: token.name,
    description: token.description || '',
    expires_at: token.expires_at ? token.expires_at.slice(0, 16) : ''
  }
  showEditor.value = true
}

async function save() {
  if (!form.value.name.trim()) {
    showToast('请输入名称')
    return
  }
  const payload = {
    name: form.value.name.trim(),
    description: form.value.description.trim() || null,
    expires_at: form.value.expires_at ? new Date(form.value.expires_at).toISOString() : null
  }
  if (editing.value) {
    await updateSystemToken(editing.value.id, payload)
    showSuccessToast('Token 已更新')
  } else {
    const created = await createSystemToken(payload)
    revealedToken.value = created.token
    showRevealed.value = true
  }
  showEditor.value = false
  await loadTokens()
}

async function toggle(token: SystemToken) {
  await updateSystemToken(token.id, { is_active: !token.is_active })
  showSuccessToast(token.is_active ? 'Token 已停用' : 'Token 已启用')
  await loadTokens()
}

async function remove(token: SystemToken) {
  try {
    await showConfirmDialog({ title: '删除系统 Token', message: `确定删除「${token.name}」吗？删除后无法恢复。` })
    await deleteSystemToken(token.id)
    showSuccessToast('Token 已删除')
    await loadTokens()
  } catch (error) {
    if (error !== 'cancel') throw error
  }
}

async function copyToken() {
  await navigator.clipboard.writeText(revealedToken.value)
  showSuccessToast('已复制')
}

onMounted(loadTokens)
</script>

<template>
  <div class="page">
    <van-nav-bar title="系统 Token" left-arrow @click-left="$router.back()" />
    <van-notice-bar wrapable :scrollable="false" text="Token 用于 MCP 等系统集成。明文只在创建时显示一次，请妥善保存。" />

    <van-pull-refresh v-model="loading" @refresh="loadTokens">
      <van-empty v-if="!loading && tokens.length === 0" description="暂无系统 Token" />
      <van-cell-group v-else inset class="token-list">
        <van-cell v-for="token in tokens" :key="token.id" :title="token.name" :label="`${token.token_prefix}… · 最近使用：${formatTime(token.last_used_at)}`">
          <template #value>
            <van-tag :type="token.is_active ? 'success' : 'default'">{{ token.is_active ? '启用' : '停用' }}</van-tag>
          </template>
          <template #extra>
            <div class="actions">
              <van-button size="mini" plain @click="openEdit(token)">编辑</van-button>
              <van-button size="mini" plain :type="token.is_active ? 'warning' : 'success'" @click="toggle(token)">{{ token.is_active ? '停用' : '启用' }}</van-button>
              <van-button size="mini" plain type="danger" @click="remove(token)">删除</van-button>
            </div>
          </template>
        </van-cell>
      </van-cell-group>
    </van-pull-refresh>

    <div class="footer"><van-button type="primary" block round icon="plus" @click="openCreate">创建系统 Token</van-button></div>

    <van-popup v-model:show="showEditor" position="bottom" round>
      <div class="editor">
        <h3>{{ editing ? '编辑系统 Token' : '创建系统 Token' }}</h3>
        <van-field v-model="form.name" label="名称" placeholder="例如：Codex MCP" required />
        <van-field v-model="form.description" label="说明" type="textarea" placeholder="用途说明（选填）" />
        <van-field v-model="form.expires_at" label="过期时间" type="datetime-local" />
        <van-button type="primary" block round @click="save">保存</van-button>
      </div>
    </van-popup>

    <van-dialog v-model:show="showRevealed" title="系统 Token 已创建" confirm-button-text="我已保存" @confirm="revealedToken = ''">
      <div class="reveal">
        <p>请立即复制，关闭后无法再次查看：</p>
        <code>{{ revealedToken }}</code>
        <van-button size="small" type="primary" block @click="copyToken">复制 Token</van-button>
      </div>
    </van-dialog>
  </div>
</template>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; padding-bottom: 88px; }
.token-list { margin-top: 12px; }
.actions { display: flex; gap: 6px; align-items: center; margin-left: 10px; }
.footer { position: fixed; left: 16px; right: 16px; bottom: 20px; }
.editor { padding: 18px 16px 28px; }
.editor h3 { text-align: center; margin: 0 0 16px; }
.editor .van-button { margin-top: 18px; }
.reveal { padding: 8px 20px 20px; }
.reveal code { display: block; overflow-wrap: anywhere; padding: 12px; margin: 10px 0; background: #f3f4f6; border-radius: 6px; }
</style>
