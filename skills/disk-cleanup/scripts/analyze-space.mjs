#!/usr/bin/env node
// Analyze disk space — find large directories quickly
// Usage: node analyze-space.mjs [target-dir] [--depth N] [--top N]

import { execSync } from 'child_process';
import { existsSync } from 'fs';

const target = process.argv[2] || process.env.HOME || process.env.USERPROFILE || '.';
const depth = parseInt(process.argv.includes('--depth') ? process.argv[process.argv.indexOf('--depth') + 1] : '1');
const topN = parseInt(process.argv.includes('--top') ? process.argv[process.argv.indexOf('--top') + 1] : '20');

if (!existsSync(target)) {
  console.error(`Path not found: ${target}`);
  process.exit(1);
}

console.log(`\n=== Disk Space Analysis: ${target} ===\n`);

// Run du and parse output
function du(path, maxDepth = 1) {
  try {
    const cmd = `du -sh "${path}"/* 2>/dev/null`;
    const out = execSync(cmd, { encoding: 'utf8', timeout: 30000, maxBuffer: 10 * 1024 * 1024 });
    return out;
  } catch {
    return '';
  }
}

// Top-level analysis
console.log(`--- Top ${topN} items ---`);
const topOut = du(target);
const lines = topOut.trim().split('\n')
  .filter(Boolean)
  .map(line => {
    const [size, ...pathParts] = line.split('\t');
    return { size, path: pathParts.join('\t') };
  })
  .filter(item => {
    // Parse size for sorting
    const num = parseFloat(item.size);
    const unit = item.size.replace(/[0-9.]/g, '').trim();
    const multipliers = { B: 1, K: 1024, M: 1024 * 1024, G: 1024 * 1024 * 1024 };
    return !isNaN(num * (multipliers[unit] || 1));
  })
  .sort((a, b) => {
    const parseSize = s => {
      const n = parseFloat(s.size);
      const u = s.size.replace(/[0-9.]/g, '').trim();
      const m = { B: 1, K: 1024, M: 1024 * 1024, G: 1024 * 1024 * 1024 };
      return n * (m[u] || 1);
    };
    return parseSize(b) - parseSize(a);
  })
  .slice(0, topN);

lines.forEach(({ size, path }) => {
  const label = path.replace(target + '/', '');
  console.log(`  ${size.padStart(8)}  ${label}`);
});

// If depth > 1, drill into largest subdirectory
if (depth > 1 && lines.length > 0) {
  const largestPath = lines[0].path;
  console.log(`\n--- Drilling into: ${largestPath.replace(target + '/', '')} ---`);
  const subOut = du(largestPath);
  const subLines = subOut.trim().split('\n').filter(Boolean).sort().reverse().slice(0, 15);
  subLines.forEach(line => {
    const [size, ...parts] = line.split('\t');
    console.log(`  ${size.padStart(8)}  ${parts.join('\t').replace(largestPath + '/', '')}`);
  });
}
