import React, {
  type ReactNode,
  useState,
  useCallback,
  useRef,
  useEffect,
  type ComponentType,
} from 'react';
import clsx from 'clsx';
import TOCItems from '@theme/TOCItems';
import type {Props} from '@theme/TOC';
import type {Props as TOCItemsBaseProps} from '@theme/TOCItems';

import styles from './styles.module.css';

const LINK_CLASS_NAME = 'table-of-contents__link toc-highlight';
const LINK_ACTIVE_CLASS_NAME = 'table-of-contents__link--active';

// swizzled 的 TOCItems 组件扩展了这两个 props，但原始模块类型未声明
type TOCItemsWithExtras = ComponentType<
  TOCItemsBaseProps & {
    allExpanded?: boolean;
    onCollapsibleCountChange?: (count: number) => void;
  }
>;
const TOCItemsEx = TOCItems as TOCItemsWithExtras;

export default function TOC({className, ...props}: Props): ReactNode {
  const [allExpanded, setAllExpanded] = useState(true);
  const [visible, setVisible] = useState(false);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const toggleAll = useCallback(() => {
    setAllExpanded((v) => !v);
  }, []);

  useEffect(() => {
    setAllExpanded(true);
    setVisible(false);
  }, [props.toc]);

  const clearHideTimer = useCallback(() => {
    if (hideTimerRef.current) {
      clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }
  }, []);

  const showPanel = useCallback(() => {
    clearHideTimer();
    setVisible(true);
  }, [clearHideTimer]);

  const hidePanel = useCallback(() => {
    clearHideTimer();
    setVisible(false);
  }, [clearHideTimer]);

  const scheduleHide = useCallback(() => {
    clearHideTimer();
    hideTimerRef.current = setTimeout(() => {
      setVisible(false);
    }, 200);
  }, [clearHideTimer]);

  useEffect(() => {
    return () => clearHideTimer();
  }, [clearHideTimer]);

  // 面板显示/隐藏时切换 body 类名，让正文右侧预留空间避免遮挡
  useEffect(() => {
    if (visible) {
      document.body.classList.add('toc-panel-visible');
    } else {
      document.body.classList.remove('toc-panel-visible');
    }
    return () => {
      document.body.classList.remove('toc-panel-visible');
    };
  }, [visible]);

  return (
    <>
      {/* 右侧 hover 触发区 */}
      <div
        className="toc-hover-zone"
        onMouseEnter={showPanel}
      />

      {/* 浮动大纲面板 */}
      <div
        className={clsx(
          styles.tableOfContents,
          'thin-scrollbar',
          className,
          'custom-toc-float',
          visible && 'custom-toc-float--visible',
        )}
        onMouseEnter={showPanel}
        onMouseLeave={scheduleHide}
      >
        {/* 头部 */}
        <div className="toc-header">
          <span className="toc-header__title">大纲</span>
          <div className="toc-header__actions">
            {/* 隐藏大纲按钮 */}
            <button
              type="button"
              className="toc-header__btn toc-header__btn--hide"
              aria-label="隐藏大纲"
              title="隐藏大纲"
              onClick={hidePanel}
            >
              {/* eye-off 图标 */}
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
                <line x1="1" y1="1" x2="23" y2="23" />
              </svg>
            </button>
            {/* 全部展开/折叠按钮 */}
            <button
              type="button"
              className={clsx('toc-header__btn', 'toc-header__btn--toggle-all', {
                'toc-header__btn--active': !allExpanded,
              })}
              aria-label={allExpanded ? '全部折叠' : '全部展开'}
              title={allExpanded ? '全部折叠' : '全部展开'}
              onClick={toggleAll}
            >
              {/* 列表视图图标 ≡ */}
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M3 6h2v2H3V6zm4 0h14v2H7V6zm0 5h14v2H7v-2zm0 5h14v2H7v-2zM3 11h2v2H3v-2zm0 5h2v2H3v-2z" />
              </svg>
            </button>
          </div>
        </div>

        <TOCItemsEx
          {...props}
          linkClassName={LINK_CLASS_NAME}
          linkActiveClassName={LINK_ACTIVE_CLASS_NAME}
          allExpanded={allExpanded}
          onCollapsibleCountChange={() => {}}
        />
      </div>
    </>
  );
}
