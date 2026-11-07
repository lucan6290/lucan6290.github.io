import { getProcessor } from 'bytemd';
import breaks from '@bytemd/plugin-breaks';
import gfm from '@bytemd/plugin-gfm';
import math from '@bytemd/plugin-math';
import { transformDocusaurusAdmonitions } from '../../src/utils/markdownAdmonitions.js';
import { headingAnchor, resolvePublicMarkdownLink } from '../../src/utils/publicPaths.ts';

function text(node) {
  return node.value || node.children?.map(text).join('') || '';
}

export function renderPublicMarkdown(article, { base, assets, title }) {
  const content = {
    remark: processor => processor.use(() => tree => {
      const first = tree.children[0];
      if (title && first?.type === 'heading' && first.depth === 1 && text(first) === title) {
        tree.children.shift();
      }
      function visit(node) {
        if (node.url && ['image', 'link', 'definition'].includes(node.type)) {
          node.url = resolvePublicMarkdownLink(node.url, article.relativePath, assets, base);
        }
        node.children?.forEach(visit);
      }
      visit(tree);
    }),
    rehype: processor => processor.use(() => tree => {
      const used = new Set();
      function visit(node) {
        if (node.type === 'element' && /^h[1-6]$/.test(node.tagName)) {
          node.properties.id = headingAnchor(text(node), used);
        }
        if (node.type === 'element' && node.tagName === 'blockquote') {
          const paragraph = node.children.find(child => child.type === 'element');
          const strong = paragraph?.tagName === 'p' && paragraph.children.find(child => child.tagName === 'strong');
          const label = strong && strong.children[0];
          const marker = label?.type === 'text' && /^\[!(note|tip|info|warning|danger)\]\s*/i.exec(label.value);
          if (marker) {
            node.properties.className = ['md-admonition', `md-admonition--${marker[1].toLowerCase()}`];
            label.value = label.value.slice(marker[0].length);
          }
        }
        node.children?.forEach(visit);
      }
      visit(tree);
    }),
  };
  return getProcessor({ plugins: [gfm(), math(), breaks(), content] })
    .processSync(transformDocusaurusAdmonitions(article.rawContent))
    .toString();
}
