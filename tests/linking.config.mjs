/** @type {import('internal-linking').LinkingConfig} */
export default {
  siteName: 'DiggingScriptures',
  siteUrl: 'https://diggingscriptures.com',
  distDir: './dist',
  pageTypes: [
    { name: 'hub', pattern: /^\/journeys\/[^/]+\/$/, role: 'hub', minLinksOut: 5, maxLinksOut: 15 },
    { name: 'story', pattern: /^\/stories\//, role: 'spoke', minLinksOut: 3, maxLinksOut: 8 },
    { name: 'place', pattern: /^\/places\//, role: 'spoke', minLinksOut: 3, maxLinksOut: 8 },
    { name: 'route', pattern: /^\/routes\//, role: 'spoke', minLinksOut: 3, maxLinksOut: 8 },
    { name: 'context', pattern: /^\/context\//, role: 'bridge', minLinksOut: 3, maxLinksOut: 8 },
    { name: 'homepage', pattern: /^\/$/, role: 'static' },
  ],
  excludePaths: [/^\/_astro\//, /^\/blobs\//],
  bodySelector: 'main, article',
  excludeSelectors: ['nav', 'header', 'footer'],
  clusterStrategy: 'hub-frontmatter',
  contentDirs: ['src/content/hubs', 'src/content/stories', 'src/content/places', 'src/content/routes'],
};
