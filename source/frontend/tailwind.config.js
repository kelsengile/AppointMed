/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#effaf8",
          100: "#d3f1ec",
          500: "#14917f",
          600: "#0f7b6c",
          700: "#0d6459",
          900: "#12302f",
        },
      },
    },
  },
  plugins: [],
};
