/** @type { import('@storybook/svelte').StorybookConfig } */
const config = {
  stories: ['../src/**/*.stories.@(js|jsx|mjs|ts|tsx|svelte)'],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-docs',
  ],
  framework: {
    name: '@storybook/svelte-vite',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
};
export default config;