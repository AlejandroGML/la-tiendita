/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['selector', '[class~="dark-theme"]'],
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {},
  },
  plugins: [require('tailwindcss-primeui')],
};
