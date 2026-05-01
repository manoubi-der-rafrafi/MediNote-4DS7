export const tailwindConfig = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0E0E10",
        s1: "#18181C",
        s2: "#22222A",
        s3: "#2A2A35",
        bd: "rgba(255,255,255,0.08)",
        manager: "#A78BFA",
        marketing: "#FB923C",
        direction: "#F87171",
        blue: "#4F8EF7",
        teal: "#2DD4BF",
        green: "#34D399",
        gold: "#FBBF24",
        red: "#F87171",
      },
    },
  },
  plugins: [],
};

module.exports = tailwindConfig;
