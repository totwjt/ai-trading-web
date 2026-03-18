export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // 使用 CSS 变量，支持主题切换
        primary: 'rgb(var(--color-primary) / <alpha-value>)',
        up: 'rgb(var(--color-up) / <alpha-value>)',
        down: 'rgb(var(--color-down) / <alpha-value>)',
        border: 'rgb(var(--color-border) / <alpha-value>)',
        bgMain: 'rgb(var(--color-bg-main) / <alpha-value>)',
        card: 'rgb(var(--color-card) / <alpha-value>)',
        textMain: 'rgb(var(--color-text-main) / <alpha-value>)',
        textSub: 'rgb(var(--color-text-sub) / <alpha-value>)',
        textMute: 'rgb(var(--color-text-mute) / <alpha-value>)',
      },
      fontSize: {
        xxs: '0.7rem',
      },
      fontFamily: {
        sans: ['PingFang SC', 'Microsoft YaHei', 'sans-serif'],
        numeric: ['Helvetica Neue', 'Arial', 'sans-serif']
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries'),
  ],
}
