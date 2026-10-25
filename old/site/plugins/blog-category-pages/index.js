const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');

const BLOG_DATE_PREFIX = /^\d{4}-\d{2}-\d{2}-/;

function parseBlogSidebars(siteDir) {
  const sidebarsPath = path.join(siteDir, 'blogSidebars.ts');
  if (!fs.existsSync(sidebarsPath)) {
    return [];
  }
  const content = fs.readFileSync(sidebarsPath, 'utf-8');
  const items = [];
  const objectPattern = /\{([\s\S]*?)\}/g;
  let match;
  while ((match = objectPattern.exec(content)) !== null) {
    const body = match[1];
    const pathMatch = body.match(/\bpath\s*:\s*['"]([^'"]+)['"]/);
    if (!pathMatch) {
      continue;
    }
    const labelMatch = body.match(/\blabel\s*:\s*['"]([^'"]+)['"]/);
    const toMatch = body.match(/\bto\s*:\s*['"]([^'"]+)['"]/);
    const countMatch = body.match(/\bcount\s*:\s*(\d+)/);
    items.push({
      label: labelMatch?.[1] || pathMatch[1],
      path: pathMatch[1],
      to: toMatch?.[1] || `/blog/${pathMatch[1]}`,
      count: countMatch ? Number(countMatch[1]) : undefined,
    });
  }
  return items;
}

function blogPostPermalink(frontMatter, filename) {
  const slug = String(frontMatter.slug || '').trim() || path.basename(filename, path.extname(filename)).replace(BLOG_DATE_PREFIX, '');
  return `/blog/${slug.replace(/^\/+/, '')}`;
}

function readCategoryPosts(siteDir, categoryPath) {
  const categoryDir = path.join(siteDir, 'blog', categoryPath);
  if (!fs.existsSync(categoryDir) || !fs.statSync(categoryDir).isDirectory()) {
    return [];
  }
  return fs
    .readdirSync(categoryDir)
    .filter((filename) => /\.(md|mdx)$/i.test(filename) && !/^index\.mdx?$/i.test(filename))
    .map((filename) => {
      const absolutePath = path.join(categoryDir, filename);
      const parsed = matter(fs.readFileSync(absolutePath, 'utf-8'));
      const frontMatter = parsed.data || {};
      return {
        title: frontMatter.title || path.basename(filename, path.extname(filename)),
        description: frontMatter.description || '',
        date: frontMatter.date || '',
        permalink: blogPostPermalink(frontMatter, filename),
        tags: Array.isArray(frontMatter.tags) ? frontMatter.tags : [],
      };
    })
    .sort((left, right) => String(right.date).localeCompare(String(left.date)));
}

module.exports = function blogCategoryPagesPlugin(context) {
  const {siteDir} = context;

  return {
    name: 'blog-category-pages',
    async contentLoaded({actions}) {
      const {addRoute, createData} = actions;
      const categories = parseBlogSidebars(siteDir);

      await Promise.all(
        categories.map(async (category) => {
          const data = {
            category,
            posts: readCategoryPosts(siteDir, category.path),
          };
          const dataPath = await createData(
            `blog-category-${encodeURIComponent(category.path)}.json`,
            JSON.stringify(data, null, 2),
          );
          addRoute({
            path: category.to,
            exact: true,
            component: '@site/src/components/BlogCategoryPage',
            modules: {
              categoryData: dataPath,
            },
          });
        }),
      );
    },
  };
};
