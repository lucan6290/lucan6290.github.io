'use strict';

hexo.extend.filter.register('before_generate', function() {
  const isProduction = !process.argv.includes('server') && !process.argv.includes('s');
  
  if (isProduction) {
    const posts = hexo.locals.get('posts');
    const filteredPosts = posts.filter(post => {
      const status = post.status || 'published';
      if (status === 'draft') {
        hexo.log.info(`[内容分级] 排除草稿文章: ${post.title}`);
        return false;
      }
      return true;
    });
    hexo.locals.set('posts', filteredPosts);
  }
});

hexo.extend.filter.register('before_post_render', function(data) {
  if (data.status === 'wip') {
    data.wip = true;
    const wipBanner = '<div class="wip-banner">这篇文章正在施工中，内容可能不完整或有待完善，请谨慎参考。</div>\n\n';
    data.content = wipBanner + data.content;
  }
  return data;
});
