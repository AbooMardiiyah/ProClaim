/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        teal: {
          DEFAULT: "#028090",
          50: "#f0fafa",
          400: "#02A3B5",
          500: "#028090",
          600: "#026070",
        },
        navy: {
          DEFAULT: "#0A2342",
        },
        mint: {
          DEFAULT: "#02C39A",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
