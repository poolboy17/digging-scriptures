/** @type {import('shared-test-utils').SiteConfig} */
export default {
  siteName: 'DiggingScriptures',
  distDir: './dist',

  // This site has 5 content collections: journeys, places, routes, stories, context.
  // Pages live at dist/journeys/some-slug/, dist/places/some-slug/, etc.
  // Match any path like "collection/slug" inside dist/.
  pagePattern: /^(journeys|places|routes|stories|context)\/.+$/,

  // Use recursive discovery to find pages inside collection directories
  discoverOpts: { recursive: true },

  excludeDirs: ['_astro', 'blobs'],

  checks: {
    duplicateIds: true,
    headingHierarchy: true,
    headTags: {
      requireCanonical: true,
      requireOgImage: true,
      requireDescription: true,
    },
  },
};
