/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        header: "var(--font-header)",
        body: "var(--font-body)",
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
