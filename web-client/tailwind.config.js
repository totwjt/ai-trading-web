export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // 默认主题 - 股票交易风格
        primary: '#0066FF',
        up: '#FF0000',
        down: '#00B050',
        border: '#E5E7EB',
        bgMain: '#F9FAFB',
        card: '#FFFFFF',
        textMain: '#1F2937',
        textSub: '#6B7280',
        textMute: '#9CA3AF',
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
