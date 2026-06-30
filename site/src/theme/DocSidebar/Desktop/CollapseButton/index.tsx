import React, {type ReactNode} from 'react';
import {translate} from '@docusaurus/Translate';
import type {Props} from '@theme/DocSidebar/Desktop/CollapseButton';

export default function CollapseButton({onClick}: Props): ReactNode {
  return (
    <button
      type="button"
      title={translate({
        id: 'theme.docs.sidebar.collapseButtonTitle',
        message: 'Collapse sidebar',
        description: 'The title attribute for collapse button of doc sidebar',
      })}
      aria-label={translate({
        id: 'theme.docs.sidebar.collapseButtonAriaLabel',
        message: 'Collapse sidebar',
        description: 'The title attribute for collapse button of doc sidebar',
      })}
      className="toggle-sidebar-wrapper toggle-sidebar-wrapper--collapse"
      onClick={onClick}>
      <span className="arrow end" />
    </button>
  );
}
