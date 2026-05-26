const fs = require('fs');
const path = require('path');

const postsDir = path.join(__dirname, 'source/_posts');
const files = fs.readdirSync(postsDir).filter(f => f.endsWith('.md'));

console.log(`找到 ${files.length} 篇文章，开始处理...`);

let processed = 0;

files.forEach(file => {
  const filePath = path.join(postsDir, file);
  let content = fs.readFileSync(filePath, 'utf8');
  
  if (content.includes('cover:')) {
    const beforeContent = content;
    content = content.replace(/\ncover:.*?(\n|$)/g, '\n');
    if (content !== beforeContent) {
      fs.writeFileSync(filePath, content, 'utf8');
      console.log(`✓ 已处理: ${file}`);
      processed++;
    }
  }
});

console.log(`\n完成！共处理了 ${processed} 篇文章。`);
