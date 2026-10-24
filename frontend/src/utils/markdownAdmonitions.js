const DEFAULT_TITLES = {
  note: '说明',
  tip: '提示',
  info: '信息',
  warning: '注意',
  danger: '危险',
};

const OPENING = /^\s{0,3}:::(note|tip|info|warning|danger)(?:\s*\[([^\]]+)\])?\s*$/i;
const FENCE_START = /^\s{0,3}(`{3,}|~{3,})/;
const FENCE_END = /^\s{0,3}(`+|~+)\s*$/;

export function transformDocusaurusAdmonitions(markdown) {
  const output = [];
  const admonitions = [];
  let fenceCharacter = '';
  let fenceLength = 0;

  for (const line of markdown.split(/\r?\n/)) {
    const quotePrefix = '>'.repeat(admonitions.length);

    if (fenceCharacter) {
      output.push(admonitions.length ? `${quotePrefix} ${line}` : line);
      const closingFence = line.match(FENCE_END);
      if (closingFence && closingFence[1][0] === fenceCharacter && closingFence[1].length >= fenceLength) {
        fenceCharacter = '';
        fenceLength = 0;
      }
      continue;
    }

    const openingFence = line.match(FENCE_START);
    if (openingFence) {
      output.push(admonitions.length ? `${quotePrefix} ${line}` : line);
      fenceCharacter = openingFence[1][0];
      fenceLength = openingFence[1].length;
      continue;
    }

    const openingAdmonition = line.match(OPENING);
    if (openingAdmonition) {
      const type = openingAdmonition[1].toLowerCase();
      const title = openingAdmonition[2]?.trim() || DEFAULT_TITLES[type];
      admonitions.push(type);
      const prefix = `${'> '.repeat(admonitions.length)}`;
      output.push(`${prefix}**[!${type}] ${title}**`);
      output.push('>'.repeat(admonitions.length));
      continue;
    }

    if (/^\s{0,3}:::\s*$/.test(line) && admonitions.length) {
      admonitions.pop();
      output.push('>'.repeat(admonitions.length));
      continue;
    }

    output.push(admonitions.length ? `${'> '.repeat(admonitions.length)}${line}` : line);
  }

  return output.join('\n');
}
