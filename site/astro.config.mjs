import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://dealspulse.pages.dev',
  integrations: [tailwind()]
});
