import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';

// ================================================================================
// ASTRO CONFIGURATION — PILGRIMAGE SITE
// ================================================================================
// MODE: Static Site Generation (SSG) ONLY
// NO SSR, NO APIs, NO CMS, NO Databases
// ================================================================================

export default defineConfig({
    // Static output mode - no server required
    output: 'static',
    
    // Vite plugins
    vite: {
        plugins: [tailwindcss()]
    },
    
    // Integrations
    integrations: [react(), sitemap()],
    
    // Build configuration
    build: {
        // Inline stylesheets for performance
        inlineStylesheets: 'auto'
    },
    
    // Site configuration
    site: 'https://diggingscriptures.com',
    
    // Trailing slashes for clean URLs
    trailingSlash: 'never'
});
