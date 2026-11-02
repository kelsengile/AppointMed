/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#EFF5FE",
          100: "#DCE9FB",
          500: "#2468CF",
          600: "#0B52B5",
          700: "#06408F",
          900: "#05316E",
        },
      },
    },
  },
  plugins: [],
};
