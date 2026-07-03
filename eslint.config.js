import globals from "globals";
import tseslint from "typescript-eslint";

export default [
  { files: ["**/*.{ts,tsx}"] },
  { languageOptions: { globals: globals.browser } },
  ...tseslint.configs.recommended,
  {
    rules: {
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
    },
  },
];
