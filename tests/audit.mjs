/**
 * DiggingScriptures — Site Audit Runner
 * Uses shared-test-utils for all heavy lifting.
 */
import { readFileSync } from 'fs';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';
import {
  discoverPages,
  createRunner,
  createResults,
  printReport,
  getExitCode,
} from 'shared-test-utils';
import config from './site.config.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const distDir = resolve(__dirname, '..', config.distDir);
const pages = discoverPages(distDir, config.pagePattern, config.excludeDirs, config.discoverOpts);
const run = createRunner(config);
const results = createResults();

console.log(`\n  ${config.siteName} Audit — scanning dist/ ...\n`);
console.log(`  Found ${pages.length} pages\n`);

if (pages.length === 0) {
  console.error('\x1b[31mNo pages found in dist/. Run "npm run build" first.\x1b[0m');
  process.exit(1);
}

for (const { name, path } of pages) {
  const html = readFileSync(path, 'utf-8');
  run(html, name, results);
}

printReport(config.siteName, results);
process.exit(getExitCode(results));
