'use strict';

hexo.extend.filter.register('before_post_render', function(data) {
  const categoryCovers = {
    '技术研习': '/img/covers/tech-study.svg',
    '踩坑复盘': '/img/covers/pitfall-review.svg',
    '项目实战': '/img/covers/project-practice.svg',
    '成长随笔': '/img/covers/growth-essay.svg',
    '资源分享': '/img/covers/resource-sharing.svg'
  };

  const categories = data.categories;
  if (!categories || !categories.data || !categories.data.length) return data;

  const primaryCategory = categories.data[0].name;

  if (primaryCategory && categoryCovers[primaryCategory]) {
    data.cover = categoryCovers[primaryCategory];
  }

  return data;
});
