// Authoring-only renderer: the delivered HTML needs neither Node nor a CDN.
const fs = require('fs');
const path = require('path');
const katex = require(path.join(__dirname, '../vendor/katex/dist/katex.js'));
const equations = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(equations.map(({tex, display}) =>
  katex.renderToString(tex, {displayMode: display, output: 'htmlAndMathml',
    throwOnError: true, strict: 'error', trust: false}))));
