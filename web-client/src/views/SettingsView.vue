<script setup lang="ts">
import { ref } from 'vue'

// 用户信息
const userInfo = ref({
  name: '量化交易员',
  level: 'LV.5 资深用户',
  email: 'trader@example.com',
  phone: '138****8888'
})

// 设置选项
const settings = ref({
  theme: 'light',
  language: 'zh-CN',
  notifications: {
    priceAlert: true,
    newsAlert: true,
    tradeAlert: true
  },
  trading: {
    defaultQuantity: 100,
    autoConfirm: false,
    soundAlert: true
  }
})

// 修改密码表单
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})
</script>

<template>
  <div class="min-h-screen bg-bgMain p-6">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-xl font-bold text-textMain">设置</h1>
        <p class="text-sm text-textMute">个性化您的交易体验</p>
      </div>

      <!-- User Profile Section -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-6">
        <h3 class="font-bold text-sm mb-4">个人资料</h3>
        <div class="flex items-center space-x-4">
          <img 
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuAUFRuvDVoYwMUzc9WD6lbtldY6E2S3YU40H94c5xFAL7OKTWcd6QzPLNF-sF6b-J5-KFJAfin_7dzq0ZLEkrxaaqz1XQI1fIwB_4QgQrJXWQsfoVx10pixf2Akf7YyWxIDqe9vcPERa0dFSOqZc01gi-sDWoDRc8R9aFLACUfuHPfEUCHlve-WAXyhnpGIvwIi1aCJIdywpuj1Yn_rCCPXY3f0yKZA6bwW6vZbG7BYu-hCQlkT4S8Ya5p_-UHLozijfzB-FcTyFdUF" 
            alt="Avatar" 
            class="w-16 h-16 rounded-full border border-gray-200"
          />
          <div>
            <p class="font-bold text-textMain">{{ userInfo.name }}</p>
            <p class="text-xs text-textMute">{{ userInfo.level }}</p>
            <p class="text-xs text-textMute mt-1">{{ userInfo.email }}</p>
          </div>
          <button class="ml-auto px-4 py-2 border border-gray-200 text-textMain text-sm font-bold rounded hover:bg-gray-50 transition-colors">
            编辑资料
          </button>
        </div>
      </div>

      <!-- Appearance Section -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-6">
        <h3 class="font-bold text-sm mb-4">外观设置</h3>
        <div class="space-y-4">
          <div class="flex justify-between items-center">
            <div>
              <p class="font-medium text-textMain">主题</p>
              <p class="text-xs text-textMute">选择界面主题颜色</p>
            </div>
            <div class="flex gap-2">
              <button 
                :class="[
                  'px-4 py-2 text-sm font-bold rounded transition-all',
                  settings.theme === 'light' ? 'bg-primary text-white' : 'bg-gray-100 text-textMain'
                ]"
              >
                浅色
              </button>
              <button 
                :class="[
                  'px-4 py-2 text-sm font-bold rounded transition-all',
                  settings.theme === 'dark' ? 'bg-primary text-white' : 'bg-gray-100 text-textMain'
                ]"
              >
                深色
              </button>
            </div>
          </div>
          
          <div class="flex justify-between items-center">
            <div>
              <p class="font-medium text-textMain">语言</p>
              <p class="text-xs text-textMute">界面显示语言</p>
            </div>
            <select 
              v-model="settings.language"
              class="px-4 py-2 border border-gray-200 rounded text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
            >
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Notifications Section -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-6">
        <h3 class="font-bold text-sm mb-4">通知设置</h3>
        <div class="space-y-4">
          <div class="flex justify-between items-center">
            <div>
              <p class="font-medium text-textMain">价格提醒</p>
              <p class="text-xs text-textMute">股票价格达到设定值时提醒</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="settings.notifications.priceAlert" class="sr-only peer">
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
          
          <div class="flex justify-between items-center">
            <div>
              <p class="font-medium text-textMain">新闻提醒</p>
              <p class="text-xs text-textMute">重要财经新闻推送</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="settings.notifications.newsAlert" class="sr-only peer">
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
          
          <div class="flex justify-between items-center">
            <div>
              <p class="font-medium text-textMain">交易提醒</p>
              <p class="text-xs text-textMute">订单成交、撤单等通知</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="settings.notifications.tradeAlert" class="sr-only peer">
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        </div>
      </div>

      <!-- Trading Settings Section -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-6">
        <h3 class="font-bold text-sm mb-4">交易设置</h3>
        <div class="space-y-4">
          <div class="flex justify-between items-center">
            <div>
              <p class="font-medium text-textMain">默认数量</p>
              <p class="text-xs text-textMute">下单时的默认数量</p>
            </div>
            <input 
              type="number" 
              v-model="settings.trading.defaultQuantity"
              class="w-24 px-3 py-2 border border-gray-200 rounded text-sm text-right focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>
          
          <div class="flex justify-between items-center">
            <div>
              <p class="font-medium text-textMain">自动确认</p>
              <p class="text-xs text-textMute">下单时跳过确认对话框</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="settings.trading.autoConfirm" class="sr-only peer">
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
          
          <div class="flex justify-between items-center">
            <div>
              <p class="font-medium text-textMain">声音提醒</p>
              <p class="text-xs text-textMute">交易操作时播放提示音</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="settings.trading.soundAlert" class="sr-only peer">
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        </div>
      </div>

      <!-- Security Section -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 p-6">
        <h3 class="font-bold text-sm mb-4">安全设置</h3>
        <div class="space-y-4">
          <div>
            <p class="font-medium text-textMain mb-2">修改密码</p>
            <div class="grid grid-cols-3 gap-4">
              <input 
                type="password" 
                v-model="passwordForm.currentPassword"
                placeholder="当前密码"
                class="px-3 py-2 border border-gray-200 rounded text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
              <input 
                type="password" 
                v-model="passwordForm.newPassword"
                placeholder="新密码"
                class="px-3 py-2 border border-gray-200 rounded text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
              <input 
                type="password" 
                v-model="passwordForm.confirmPassword"
                placeholder="确认新密码"
                class="px-3 py-2 border border-gray-200 rounded text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>
            <button class="mt-3 px-4 py-2 bg-primary text-white text-sm font-bold rounded hover:bg-blue-600 transition-colors">
              修改密码
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>