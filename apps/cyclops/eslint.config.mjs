import { FlatCompat } from "@eslint/eslintrc";

// eslint-config-next is still an eslintrc-style shareable config; FlatCompat
// adapts it to ESLint 9's flat config without pinning ESLint back to 8.
const compat = new FlatCompat({ baseDirectory: import.meta.dirname });

const config = [
  { ignores: [".next/**", "node_modules/**", "next-env.d.ts"] },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },
];

export default config;
