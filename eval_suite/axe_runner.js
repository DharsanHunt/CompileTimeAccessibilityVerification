/**
 * Axe-core evaluation runner using JSDOM.
 * Usage: node axe_runner.js <path-to-html-file> [<path-to-html-file-2> ...]
 */

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');
const axe = require('axe-core');

async function auditFile(filePath) {
  const htmlContent = fs.readFileSync(filePath, 'utf8');
  const dom = new JSDOM(htmlContent, {
    runScripts: 'dangerously',
    resources: 'usable',
  });

  const { window } = dom;
  const { document } = window;

  // Run axe-core with relevant component rules (excluding page-level HTML document rules)
  const results = await axe.run(document.body, {
    runOnly: {
      type: 'rule',
      values: ['button-name', 'label', 'input-button-name', 'tabindex', 'aria-valid-attr-value'],
    },
  });

  const simplifiedViolations = results.violations.map(v => ({
    id: v.id,
    impact: v.impact,
    description: v.description,
    help: v.help,
    nodes: v.nodes.map(n => ({
      target: n.target,
      html: n.html,
      failureSummary: n.failureSummary,
    })),
  }));

  return {
    file: path.basename(filePath),
    violations: simplifiedViolations,
    violationCount: simplifiedViolations.length,
  };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Usage: node axe_runner.js <html-file-1> ...');
    process.exit(1);
  }

  const reports = [];
  for (const f of args) {
    try {
      const report = await auditFile(f);
      reports.push(report);
    } catch (err) {
      reports.push({
        file: path.basename(f),
        error: err.message,
        violations: [],
        violationCount: 0,
      });
    }
  }

  console.log(JSON.stringify(reports, null, 2));
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
