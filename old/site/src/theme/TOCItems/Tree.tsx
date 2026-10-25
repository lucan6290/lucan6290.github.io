import React, {type ReactNode, useState, useEffect} from 'react';
import Link from '@docusaurus/Link';
import type {Props} from '@theme/TOCItems/Tree';

interface TreeProps extends Props {
  allExpanded?: boolean;
  onCollapsibleCountChange?: (count: number) => void;
  level?: number;
}

function TOCItemTree({
  toc,
  className,
  linkClassName,
  isChild,
  allExpanded,
  onCollapsibleCountChange,
  level = 0,
}: TreeProps): ReactNode {
  if (!toc.length) {
    return null;
  }
  return (
    <ul className={isChild ? 'toc-tree-children' : className}>
      {toc.map((heading) => (
        <TOCItem
          key={heading.id}
          heading={heading}
          linkClassName={linkClassName}
          allExpanded={allExpanded}
          onCollapsibleCountChange={onCollapsibleCountChange}
          level={level}
        />
      ))}
    </ul>
  );
}

interface TOCItemProps {
  heading: {
    id: string;
    value: string;
    children: Array<{id: string; value: string; children: unknown[]}>;
  };
  linkClassName?: string;
  allExpanded?: boolean;
  onCollapsibleCountChange?: (count: number) => void;
  level: number;
}

function TOCItem({
  heading,
  linkClassName,
  allExpanded,
  onCollapsibleCountChange,
  level,
}: TOCItemProps) {
  const hasChildren = heading.children && heading.children.length > 0;
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    if (allExpanded !== undefined) {
      setExpanded(allExpanded);
    }
  }, [allExpanded]);

  useEffect(() => {
    if (hasChildren && onCollapsibleCountChange) {
      onCollapsibleCountChange(1);
      return () => onCollapsibleCountChange(-1);
    }
  }, [hasChildren, onCollapsibleCountChange]);

  const toggle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setExpanded((v) => !v);
  };

  return (
    <li
      className={
        'toc-tree-item' +
        (hasChildren ? ' toc-tree-item--collapsible' : '') +
        (hasChildren && !expanded ? ' toc-tree-item--collapsed' : '') +
        ` toc-tree-item--level-${level}`
      }>
      {hasChildren ? (
        <button
          type="button"
          className={`toc-tree-toggle toc-tree-toggle--level-${level}`}
          aria-label={expanded ? '折叠' : '展开'}
          onClick={toggle}
        >
          {/* 展开：向下 ▼；折叠：向右 ▶。使用内联 SVG 三角形 */}
          <svg
            className="toc-tree-chevron toc-tree-chevron--down"
            viewBox="0 0 16 16"
            fill="currentColor"
          >
            <path d="M4 6l4 4 4-4H4z" />
          </svg>
        </button>
      ) : (
        <span className="toc-tree-spacer" />
      )}
      <Link
        to={`#${heading.id}`}
        className={linkClassName ?? undefined}
        dangerouslySetInnerHTML={{__html: heading.value}}
      />
      {hasChildren && (
        <TOCItemTree
          isChild
          toc={heading.children}
          linkClassName={linkClassName}
          allExpanded={allExpanded}
          level={level + 1}
        />
      )}
    </li>
  );
}

export default React.memo(TOCItemTree);
