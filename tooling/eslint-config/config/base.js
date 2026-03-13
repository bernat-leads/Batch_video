import * as fs from "node:fs";
import * as path from "node:path";
import { includeIgnoreFile } from "@eslint/compat";
import eslint from "@eslint/js";
import prettierConfig from "eslint-config-prettier";
import importPlugin from "eslint-plugin-import";
import turboPlugin from "eslint-plugin-turbo";
import unusedImportsPlugin from "eslint-plugin-unused-imports";
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";

// Safely include .gitignore file if it exists
const gitignorePath = path.join(import.meta.dirname, "../../../.gitignore");
const gitignoreConfig = fs.existsSync(gitignorePath)
  ? includeIgnoreFile(gitignorePath)
  : { ignores: ["node_modules/**", "dist/**", ".next/**", ".turbo/**"] };

/**
 * All packages that leverage t3-env should use this rule
 */
export const restrictEnvAccess = defineConfig([
  { ignores: ["**/env.ts"] },
  {
    files: ["**/*.js", "**/*.ts", "**/*.tsx"],
    rules: {
      "no-restricted-properties": [
        "error",
        {
          object: "process",
          property: "env",
          message: "Use `import { env } from '@/env'` instead to ensure validated types.",
        },
      ],
      "no-restricted-imports": [
        "error",
        {
          name: "process",
          importNames: ["env"],
          message: "Use `import { env } from '@/env'` instead to ensure validated types.",
        },
      ],
    },
  },
]);

export default defineConfig([
  // Ignore files not tracked by VCS and any config files
  gitignoreConfig,
  { ignores: ["**/*.config.*"] },
  {
    files: ["**/*.js", "**/*.ts", "**/*.tsx"],
    plugins: {
      import: importPlugin,
      turbo: turboPlugin,
      "unused-imports": unusedImportsPlugin,
    },
    extends: [
      eslint.configs.recommended,
      ...tseslint.configs.recommended,
      ...tseslint.configs.recommendedTypeChecked,
      ...tseslint.configs.stylisticTypeChecked,
      prettierConfig,
    ],
    rules: {
      ...turboPlugin.configs.recommended.rules,
      "@typescript-eslint/no-unused-vars": "off",
      "unused-imports/no-unused-imports": "error",
      "unused-imports/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/consistent-type-imports": [
        "warn",
        { prefer: "type-imports", fixStyle: "separate-type-imports" },
      ],
      "@typescript-eslint/no-misused-promises": [2, { checksVoidReturn: { attributes: false } }],
      "@typescript-eslint/no-unnecessary-condition": [
        "error",
        {
          allowConstantLoopConditions: true,
        },
      ],
      "@typescript-eslint/no-non-null-assertion": "error",
      "import/consistent-type-specifier-style": ["error", "prefer-top-level"],
    },
  },
  {
    linterOptions: { reportUnusedDisableDirectives: true },
    languageOptions: { parserOptions: { projectService: true } },
  },
]);
