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
    integrations: [
        react(),
        sitemap({
            changefreq: 'weekly',
            priority: 0.7,
            lastmod: new Date(),
            serialize(item) {
                // Boost hub and homepage priority
                if (item.url === 'https://diggingscriptures.com/') {
                    item.priority = 1.0;
                    item.changefreq = 'daily';
                } else if (item.url.includes('/journeys/') && item.url !== 'https://diggingscriptures.com/journeys') {
                    item.priority = 0.9;
                    item.changefreq = 'weekly';
                } else if (/\/(journeys|places|routes|stories|context)$/.test(item.url)) {
                    item.priority = 0.8;
                    item.changefreq = 'weekly';
                } else if (/\/(privacy|terms|affiliate-disclaimer|contact)$/.test(item.url)) {
                    item.priority = 0.3;
                    item.changefreq = 'yearly';
                }
                return item;
            }
        }),
    ],
    
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
