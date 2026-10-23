#!/usr/bin/env node
/**
 * CLI 入口：直接执行内容管线构建。
 * 核心实现在 ./lib/buildContent.mjs（无 shebang，可被 Vite 插件安全 import）。
 */
import { build } from './lib/buildContent.mjs';
build();
