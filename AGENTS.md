# AI Trading Web - AGENTS.md

This file contains guidelines for AI agents working on the AI Trading Web project.

## 1. Project Overview

**Tech Stack:**
- Vue 3.4.21 (Composition API)
- Vite 5.2.10
- TypeScript 5.4.5
- Tailwind CSS 3.4.4
- Pinia (State Management)
- Vue Router 4.3.2
- Ant Design Vue 4.1.2 (UI Components)

**Architecture:**
- Frontend: `web-client/` (Vue 3 + Vite)
- Backend Services: `backend/`
  - `gateway/` - API 网关
  - `data_sync/` - 数据同步服务
  - `strategy/` - 策略管理服务
  - `backtest/` - 回测服务
  - `trading/` - 交易服务
  - `ai/` - AI 分析服务

## 2. Build & Development Commands

Since no `package.json` exists yet, these commands will be used once initialized:

**Development:**
```bash
pnpm dev
# or
npm run dev
```

**Build:**
```bash
pnpm build
# or
npm run build
```

**Preview:**
```bash
pnpm preview
# or
npm run preview
```

**Linting & Formatting:**
```bash
pnpm lint
pnpm format
```

**Testing:**
```bash
pnpm test
# Run single test file:
pnpm test path/to/test.spec.ts
# Run single test case by name:
pnpm test -t "test name"
# Run tests in watch mode:
pnpm test --watch
```

## 3. Code Style Guidelines

### 3.1 TypeScript & Imports

**Imports:**
- Use absolute imports from `@/` for project files.
- Group imports: external libraries -> internal modules -> types/styles.
- Use `type` imports for types only.

```typescript
// Good
import { ref, computed } from 'vue';
import type { User } from '@/types/user';
import { useUserStore } from '@/stores/user';
import '@/styles/global.css';

// Bad
import { ref, computed, type User } from 'vue'; // Mixed
```

### 3.2 Naming Conventions

- **Components**: PascalCase (e.g., `StockChart.vue`)
- ** composables**: camelCase with `use` prefix (e.g., `useStockData`)
- **Stores**: camelCase with `Store` suffix (e.g., `userStore`)
- **Variables/Functions**: camelCase
- **Constants**: UPPER_SNAKE_CASE
- **Interfaces/Types**: PascalCase

### 3.3 Vue Component Structure

Use `<script setup>` syntax:

```vue
<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  symbol: string;
}>();

const price = ref(0);
</script>

<template>
  <div class="stock-price">{{ price }}</div>
</template>
```

### 3.4 Tailwind CSS & UI Rules

**Strictly follow `design/UI_RULES.md`:**
- **Colors**: Use semantic colors (`primary`, `up`, `down`, `textMain`, etc.). Do not use arbitrary hex codes.
- **Typography**: Use `font-numeric` for numbers (prices, percentages).
- **Spacing**: Use standard Tailwind spacing scale.
- **Density**: Use `density-table` class for high-density tables (padding: 6px 8px).
- **Rounding**: Use `rounded-lg` for cards, `rounded-xl` for modals.
- **Shadows**: `shadow-sm` for cards, `shadow-2xl` for floating panels.

**Example:**
```html
<div class="bg-card rounded-lg shadow-sm border border-gray-100 p-4">
  <span class="text-up font-numeric">+1.23%</span>
</div>
```

### 3.5 State Management (Pinia)

- Use `defineStore` with Composition API syntax.
- Keep state minimal, derive data with getters.
- Actions for async logic.

```typescript
// stores/stock.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useStockStore = defineStore('stock', () => {
  const prices = ref<Record<string, number>>({});
  const symbols = ref<string[]>([]);

  const activeSymbol = computed(() => symbols.value[0]);

  async function fetchPrices() { ... }

  return { prices, symbols, activeSymbol, fetchPrices };
});
```

### 3.6 Error Handling

- Use `try...catch` blocks for async operations.
- Display user-friendly error messages.
- Log errors to console for debugging.

### 3.7 File Organization

Follow the modular structure outlined in `docs/init.md`:

```
src/
├── assets/
├── components/
│   ├── common/
│   └── features/
├── composables/
├── router/
├── stores/
├── types/
├── utils/
└── views/
```

## 4. Special Rules for AI Agents

1.  **Read `AI_CONTEXT.md`** before starting any task.
2.  **Read `design/UI_RULES.md`** for all UI-related tasks.
3.  **Do not assume database structure**; consult `docs/DATABASE.md` if it exists.
4.  **Do not create undefined modules**.
5.  **If requirements are ambiguous**, pause and ask the user.
6.  **Achieve 100% clarity** before implementation.
7.  **Follow `docs/plan.md`** for phased development.
8.  **Update `docs/progress.md`** upon completing a phase.
9.  **Commit frequently** with descriptive messages.

### 4.1 Cursor/Copilot Integration

While this project doesn't have official Cursor or Copilot configuration files, agents should follow the rules in `AI_CONTEXT.md` and reference `design/UI_RULES.md` for UI tasks. If you need to set up Cursor rules, create `.cursorrules` in the project root.

## 5. Testing Guidelines

- Write unit tests for business logic (utils, composables, stores).
- Use Vitest (recommended for Vite projects).
- Test components using Vue Test Utils.
- Aim for high coverage on critical paths.

**Example Test:**
```typescript
// tests/utils/stockFormatter.test.ts
import { describe, it, expect } from 'vitest';
import { formatPrice } from '@/utils/stockFormatter';

describe('formatPrice', () => {
  it('formats price correctly', () => {
    expect(formatPrice(123.45)).toBe('123.45');
  });
});
```
