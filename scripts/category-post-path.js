'use strict';

const categoryPathMap = {
  'tech-study': 'tech-study',
  'pitfall-review': 'pitfall-review',
  'project-practice': 'project-practice',
  'growth-essay': 'growth-essay',
  'resource-sharing': 'resource-sharing'
};

hexo.extend.filter.register('new_post_path', function(data, replace) {
  const scaffold = data.scaffold;
  
  if (scaffold && categoryPathMap[scaffold]) {
    const path = require('path');
    const title = data.slug || data.title;
    const dir = categoryPathMap[scaffold];
    data.path = path.join(dir, title);
  }
  
  return data;
});
