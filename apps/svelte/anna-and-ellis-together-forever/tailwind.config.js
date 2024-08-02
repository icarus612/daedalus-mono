/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {},
  },
  plugins: [],
  optins: {
    safelist: [
      'basis-1/2',
      'basis-1/3',
      'basis-1/4',
      'basis-1/5',
      'basis-1/6',
    ]
  }
}

