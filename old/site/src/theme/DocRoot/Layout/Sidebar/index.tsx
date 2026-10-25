import React, {
  type ReactNode,
  useState,
  useCallback,
  useEffect,
  useRef,
} from 'react';
import clsx from 'clsx';
import {prefersReducedMotion, ThemeClassNames} from '@docusaurus/theme-common';
import {useDocsSidebar} from '@docusaurus/plugin-content-docs/client';
import {useLocation} from '@docusaurus/router';
import DocSidebar from '@theme/DocSidebar';
import ExpandButton from '@theme/DocRoot/Layout/Sidebar/ExpandButton';
import type {Props} from '@theme/DocRoot/Layout/Sidebar';

import styles from './styles.module.css';

// 侧边栏可拉伸的宽度范围（px）
const SIDEBAR_MIN_WIDTH = 240;
const SIDEBAR_MAX_WIDTH = 560;
const SIDEBAR_WIDTH_STORAGE_KEY = 'site.doc-sidebar-width';

// 读取用户上次拖拽保存的宽度（若仍在合法范围内）
function readSavedWidth(): number | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const raw = window.localStorage.getItem(SIDEBAR_WIDTH_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  const width = Number(raw);
  return Number.isFinite(width) &&
    width >= SIDEBAR_MIN_WIDTH &&
    width <= SIDEBAR_MAX_WIDTH
    ? width
    : null;
}

// Reset sidebar state when sidebar changes
// Use React key to unmount/remount the children
// See https://github.com/facebook/docusaurus/issues/3414
function ResetOnSidebarChange({children}: {children: ReactNode}) {
  const sidebar = useDocsSidebar();
  return (
    <React.Fragment key={sidebar?.name ?? 'noSidebar'}>
      {children}
    </React.Fragment>
  );
}

export default function DocRootLayoutSidebar({
  sidebar,
  hiddenSidebarContainer,
  setHiddenSidebarContainer,
}: Props): ReactNode {
  const {pathname} = useLocation();

  const [hiddenSidebar, setHiddenSidebar] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const resizeRef = useRef({startX: 0, startWidth: 0, currentWidth: 0});
  const asideRef = useRef<HTMLElement | null>(null);
  const rafRef = useRef<number | null>(null);

  // 使用 rAF 在过渡动画期间持续记录容器宽度
  const startWidthLogging = useCallback((direction: string) => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
    }
    let frame = 0;
    const tick = () => {
      const w = asideRef.current?.getBoundingClientRect().width ?? 0;
      const cs = asideRef.current
        ? getComputedStyle(asideRef.current).getPropertyValue('width').trim()
        : '';
      console.log(
        `[Sidebar] ${direction} frame=${frame}  getBoundingClientRect=${w.toFixed(1)}px  computedWidth=${cs}`,
      );
      frame++;
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const stopWidthLogging = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const toggleSidebar = useCallback(() => {
    const currentWidth = asideRef.current?.getBoundingClientRect().width ?? 0;
    const willCollapse = !hiddenSidebarContainer;
    console.log(
      `[Sidebar] toggleSidebar()  direction=${willCollapse ? '收起' : '展开'}  ` +
        `hiddenSidebar=${hiddenSidebar}  hiddenSidebarContainer=${hiddenSidebarContainer}  ` +
        `currentWidth=${currentWidth.toFixed(1)}px`,
    );

    if (hiddenSidebar) {
      setHiddenSidebar(false);
    }
    // onTransitionEnd won't fire when sidebar animation is disabled
    // fixes https://github.com/facebook/docusaurus/issues/8918
    if (!hiddenSidebar && prefersReducedMotion()) {
      setHiddenSidebar(true);
    }
    setHiddenSidebarContainer((value) => !value);

    // 开始逐帧记录宽度变化（prefers-reduced-motion 时不启动）
    if (!prefersReducedMotion()) {
      startWidthLogging(willCollapse ? '收起' : '展开');
    }
  }, [setHiddenSidebarContainer, hiddenSidebar, hiddenSidebarContainer, startWidthLogging]);

  // 恢复用户上次拖拽保存的宽度
  useEffect(() => {
    const savedWidth = readSavedWidth();
    if (savedWidth) {
      document.documentElement.style.setProperty(
        '--doc-sidebar-width',
        `${savedWidth}px`,
      );
    }
  }, []);

  // 组件卸载时停止 rAF 日志
  useEffect(() => {
    return () => stopWidthLogging();
  }, [stopWidthLogging]);

  // 开始拖拽：记录起始位置与宽度，并锁定全局光标
  const handleResizeStart = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    const container = event.currentTarget.closest<HTMLElement>(
      '.theme-doc-sidebar-container',
    );
    const startWidth = container?.getBoundingClientRect().width ?? 300;
    resizeRef.current = {
      startX: event.clientX,
      startWidth,
      currentWidth: startWidth,
    };
    document.body.classList.add('sidebar-resizing-active');
    setIsResizing(true);
  }, []);

  // 拖拽过程中监听全局 mousemove / mouseup
  useEffect(() => {
    if (!isResizing) {
      return;
    }

    const handleMouseMove = (event: MouseEvent) => {
      const {startX, startWidth} = resizeRef.current;
      const nextWidth = Math.min(
        SIDEBAR_MAX_WIDTH,
        Math.max(SIDEBAR_MIN_WIDTH, startWidth + (event.clientX - startX)),
      );
      resizeRef.current.currentWidth = nextWidth;
      document.documentElement.style.setProperty(
        '--doc-sidebar-width',
        `${nextWidth}px`,
      );
    };

    const handleMouseUp = () => {
      const {currentWidth} = resizeRef.current;
      try {
        window.localStorage.setItem(
          SIDEBAR_WIDTH_STORAGE_KEY,
          String(Math.round(currentWidth)),
        );
      } catch {
        // 忽略存储失败（如隐私模式），不影响拖拽功能
      }
      document.body.classList.remove('sidebar-resizing-active');
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.classList.remove('sidebar-resizing-active');
    };
  }, [isResizing]);

  return (
    <aside
      className={clsx(
        ThemeClassNames.docs.docSidebarContainer,
        styles.docSidebarContainer,
        hiddenSidebarContainer && styles.docSidebarContainerHidden,
        isResizing && 'sidebar-is-resizing',
      )}
      onTransitionEnd={(e) => {
        if (!e.currentTarget.classList.contains(styles.docSidebarContainer!)) {
          return;
        }

        const finalWidth = e.currentTarget.getBoundingClientRect().width;
        console.log(
          `[Sidebar] onTransitionEnd  hiddenSidebarContainer=${hiddenSidebarContainer}  finalWidth=${finalWidth.toFixed(1)}px`,
        );
        stopWidthLogging();

        if (hiddenSidebarContainer) {
          setHiddenSidebar(true);
        }
      }}
      ref={(el) => {
        asideRef.current = el;
      }}>
      <ResetOnSidebarChange>
        <div
          className={clsx(
            styles.sidebarViewport,
            hiddenSidebar && styles.sidebarViewportHidden,
          )}>
          <DocSidebar
            sidebar={sidebar}
            path={pathname}
            onCollapse={toggleSidebar}
            isHidden={hiddenSidebar}
          />
          {hiddenSidebar && <ExpandButton toggleSidebar={toggleSidebar} />}
        </div>
      </ResetOnSidebarChange>

      {!hiddenSidebarContainer && (
        <div
          className="sidebar-resize-handle"
          role="separator"
          aria-orientation="vertical"
          aria-label="拖拽调整侧边栏宽度"
          title="拖拽调整侧边栏宽度"
          onMouseDown={handleResizeStart}
        />
      )}
    </aside>
  );
}
