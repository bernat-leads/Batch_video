import baseConfig from "@tooling/eslint-config/base";
import reactConfig from "@tooling/eslint-config/react";

/** @type {import("eslint").Linter.Config[]} */
export default [...baseConfig, ...reactConfig];
