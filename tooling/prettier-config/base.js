/** @type {import("prettier").Config} */
export default {
  // Basic formatting
  semi: true,
  singleQuote: false,
  tabWidth: 2,
  useTabs: false,
  trailingComma: "es5",
  printWidth: 100,
  endOfLine: "lf",
  arrowParens: "avoid",

  // File-specific overrides
  overrides: [
    {
      files: "*.json",
      options: {
        printWidth: 120,
        trailingComma: "none",
      },
    },
    {
      files: "*.md",
      options: {
        printWidth: 80,
        proseWrap: "always",
        singleQuote: false,
      },
    },
    {
      files: "*.yaml",
      options: {
        tabWidth: 2,
        singleQuote: false,
      },
    },
    {
      files: "*.yml",
      options: {
        tabWidth: 2,
        singleQuote: false,
      },
    },
  ],

  // Plugins
  plugins: ["@ianvs/prettier-plugin-sort-imports", "prettier-plugin-tailwindcss"],

  // Import sorting configuration for @ianvs/prettier-plugin-sort-imports
  importOrder: [
    // React and framework imports
    "^(react/(.*)$)|^(react$)",
    "^(next/(.*)$)|^(next$)",

    // Third-party libraries
    "<THIRD_PARTY_MODULES>",

    // Internal workspace packages
    "^@packages/(.*)$",

    // Internal app imports
    "",
    "^types$",
    "^@/types/(.*)$",
    "^@/config/(.*)$",
    "^@/lib/(.*)$",
    "^@/hooks/(.*)$",
    "^@/utils/(.*)$",
    "^@/components/ui/(.*)$",
    "^@/components/(.*)$",
    "^@/styles/(.*)$",
    "^@/app/(.*)$",
    "^@/routes/(.*)$",

    // Relative imports
    "",
    "^[./]",
  ],

  // Tailwind CSS plugin configuration
  tailwindConfig: "./tailwind.config.*",
  tailwindFunctions: ["clsx", "cn", "cva", "twMerge"],
};
