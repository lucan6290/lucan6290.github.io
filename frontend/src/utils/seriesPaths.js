export const SERIES_ROOT = '/series';

export function hasSeriesRoute(tree) {
  return !tree.some(node => !node.article && node.path.toLowerCase() === SERIES_ROOT);
}

export function seriesHref(id) {
  return `${SERIES_ROOT}/${id}`;
}
