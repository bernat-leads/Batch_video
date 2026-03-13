import type { StorybookConfig } from '@storybook/nextjs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);

/**
 * This function is used to resolve the absolute path of a package.
 * It is needed in projects that use Yarn PnP or are set up within a monorepo.
 */
const getAbsolutePath = (value: string) =>
  dirname(require.resolve(join(value, 'package.json')));

const config: StorybookConfig = {
  stories: [
    '../stories/**/*.mdx',
    '../stories/**/*.stories.@(js|jsx|mjs|ts|tsx)',
  ],
  addons: [
    // getAbsolutePath('@storybook/addon-onboarding'),
    // getAbsolutePath('@storybook/addon-essentials'),
    // getAbsolutePath('@chromatic-com/storybook'),
    // getAbsolutePath('@storybook/addon-interactions'),
    // getAbsolutePath('@storybook/addon-themes'),
  ],
  framework: {
    name: '@storybook/nextjs',
    options: {
      builder: {
        useSWC: true, // Enables SWC support
      },
    },
  },
  staticDirs: ['../public'],
};

export default config;
