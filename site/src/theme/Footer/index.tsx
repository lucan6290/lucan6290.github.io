import React, {type ReactNode} from 'react';
import {useLocation} from '@docusaurus/router';
import OriginalFooter from '@theme-original/Footer';

export default function Footer(): ReactNode {
  const {pathname} = useLocation();
  const normalizedPathname = pathname.replace(/\/+$/, '');

  if (normalizedPathname !== '') {
    return null;
  }

  return <OriginalFooter />;
}
