import fs from 'node:fs';
import path from 'node:path';

/** 为 History 路由输出真实 HTML 入口，静态服务器无需 SPA 回退规则。 */
export function writeStaticPages({ outDir, manifest }) {
  const routes = new Set(['/about']);
  const visit = (nodes) => {
    for (const node of nodes) {
      routes.add(node.path);
      visit(node.children);
    }
  };
  visit(manifest.tree);
  const hasSection = (name) => manifest.tree.some(node => !node.article && node.name === name);
  if (!hasSection('tags')) {
    routes.add('/tags');
    for (const tag of Object.keys(manifest.tags)) routes.add('/tags/' + tag);
  }
  if (!hasSection('archive')) routes.add('/archive');

  const root = path.resolve(outDir);
  const targets = [...routes].map(route => {
    const target = path.resolve(root, '.' + route, 'index.html');
    if (!target.startsWith(root + path.sep)) throw new Error(`页面路径超出构建目录：${route}`);
    return target;
  });
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  for (const target of targets) {
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, html);
  }
  fs.writeFileSync(path.join(root, '404.html'), html);
  fs.writeFileSync(path.join(root, '.nojekyll'), '');
  return targets.length;
}
