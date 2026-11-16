// Checks the page's forward pass against PyTorch's stored numbers, and its learning step against a numerical derivative.
const fs = require('fs');
const html = fs.readFileSync('/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/extracts/2026-11-05_09-18/2026-11-05_09-18_drl_extract.html', 'utf8');
const D = JSON.parse(html.match(/<script id="nn-data"[^>]*>([\s\S]*?)<\/script>/)[1]);
const src = fs.readFileSync('drl_nn.js', 'utf8');
const pick = (name, next) => src.slice(src.indexOf('function ' + name + '('), src.indexOf(next, src.indexOf('function ' + name + '(')));
let kind = 'actor', mom = 3, net, x, sel = null, flash, fw;
const LV = ['1.6 s', '1.2 s', '1.0 s', '0.8 s'], sg = (v, d) => v.toFixed(d), $ = () => ({ textContent: '' }), paint = () => {}, edges = () => {}, inspector = () => {}, refreshInputs = () => {}, matrix = () => {};
eval(pick('load', '  // Same computation').replace('function load', 'var load = function load') + ';' + pick('forward', 'function softmax').replace('function forward', 'var forward = function forward') + ';' + pick('softmax', 'function entropy').replace('function softmax', 'var softmax = function softmax') + ';' + pick('choice', 'function nodeName').replace('function choice', 'var choice = function choice') + ';' + pick('nudge', '  // All the weights').replace('function nudge', 'var nudge = function nudge') + ';');
let maxP = 0, maxV = 0;
for (const p of D.presets) {
  kind = 'actor'; load(); const o = forward(p.lo).a[3], q = softmax(o);
  q.forEach((v, i) => { maxP = Math.max(maxP, Math.abs(v - p.p[i])); });
  kind = 'critic'; load(); maxV = Math.max(maxV, Math.abs(forward(p.lo.concat(p.gl)).a[3][0] * D.scale - p.V));
}
console.log('forward: max |p - pytorch|', maxP.toFixed(5), ' max |V - pytorch|', maxV.toFixed(4));
kind = 'actor';
for (const A of [1, -1]) {
  load(); x = D.presets[5].lo.slice(); fw = forward(x); sel = null;
  const a = choice(), p0 = softmax(fw.a[3])[a], W0 = net.W.map(w => w.slice()), b0 = net.b.map(b => b.slice());
  const saved = D.lr; D.lr = 1e-5; nudge(A); D.lr = saved;
  let g2 = 0; net.W.forEach((w, l) => w.forEach((v, i) => { g2 += (v - W0[l][i]) ** 2; })); net.b.forEach((w, l) => w.forEach((v, i) => { g2 += (v - b0[l][i]) ** 2; })); g2 /= 1e-10;
  const p1 = softmax(forward(x).a[3])[a], actual = -A * (Math.log(p1) - Math.log(p0)), predicted = -1e-5 * g2;
  console.log('gradient check A', A, 'predicted dLoss', predicted.toExponential(4), 'actual', actual.toExponential(4), 'ratio', (actual / predicted).toFixed(4));
  load(); x = D.presets[5].lo.slice(); fw = forward(x); const before = softmax(fw.a[3])[a]; nudge(A); console.log(' one step at lr', D.lr, ': p', before.toFixed(3), '->', softmax(forward(x).a[3])[a].toFixed(3));
}
