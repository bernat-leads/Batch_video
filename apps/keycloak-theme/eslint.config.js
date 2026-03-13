import baseConfig from "@tooling/eslint-config/base";
import reactConfig from "@tooling/eslint-config/react";
import storybook from "eslint-plugin-storybook";

/** @type {import("eslint").Linter.Config[]} */
export default [
    ...baseConfig,
    ...reactConfig,
    ...storybook.configs["flat/recommended"],
    {
        ignores: ["dist/**", "public/**"]
    },
    {
        rules: {
            "react-hooks/exhaustive-deps": "off",
            "@typescript-eslint/no-redeclare": "off",
            "no-labels": "off"
        }
    },
    {
        files: ["**/*.stories.*"],
        rules: {
            "import/no-anonymous-default-export": "off"
        }
    }
];
