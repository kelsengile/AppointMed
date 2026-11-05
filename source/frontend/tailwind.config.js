/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#EFF5FE",
          100: "#DCE9FB",
          200: "#BBD4F3",
          500: "#2468CF",
          600: "#0B52B5",
          700: "#06408F",
          800: "#203554",
          900: "#05316E",
          950: "#1F3655",
        },
        // Palette sampled from the landing-page Figma design (node 19:86).
        landing: {
          ink: "#1E3554", // doctor card names
          heading: "#1F3655", // big section headings
          headingalt: "#203554", // departments heading
          body: "#355882", // paragraph text
          muted: "#5079A7", // specialty / subtitle text
          soft: "#769FCB", // light blue text and dividers
          faint: "#77A0CC", // footer links
          leaf: "#16A34A", // "Available" badge
          navy: "#1E3A5F", // footer social tiles
          pagebg: "#F8FAFC",
        },
      },
    },
  },
  plugins: [],
};
