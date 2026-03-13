import reactPlugin from "eslint-plugin-react";
import reactRefresh from "eslint-plugin-react-refresh";
import { defineConfig } from "eslint/config";
import globals from "globals";

export default defineConfig([
  {
    files: ["**/*.ts", "**/*.tsx"],
    plugins: {
      react: reactPlugin,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactPlugin.configs["jsx-runtime"].rules,
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
    },
    languageOptions: {
      globals: {
        React: "writable",
        ...globals.browser,
      },
    },
    settings: {
      react: {
        version: "detect",
      },
    },
  },
]);
