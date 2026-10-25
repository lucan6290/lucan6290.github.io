#!/usr/bin/env node
/**
 * 版本号管理脚本（admin-desktop，Tauri 2 + Vue 3）。
 *
 * 同步 Vue 前端（package.json）+ Rust 后端（src-tauri/Cargo.toml）的版本号，
 * 并同步 package-lock.json。
 *
 * 用法：
 *   node scripts/version.mjs set <x.y.z>   设置新版本号
 *   node scripts/version.mjs check         校验各版本号文件一致
 */
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(SCRIPT_DIR, "..");
const PACKAGE_JSON = path.resolve(ROOT, "package.json");
const CARGO_TOML = path.resolve(ROOT, "src-tauri", "Cargo.toml");
const PACKAGE_LOCK_JSON = path.resolve(ROOT, "package-lock.json");

function read(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function write(filePath, contents) {
  fs.writeFileSync(filePath, contents, "utf8");
}

function getPackageJsonVersion() {
  const pkg = JSON.parse(read(PACKAGE_JSON));
  if (!pkg.version || typeof pkg.version !== "string") {
    throw new Error("package.json missing valid version");
  }
  return pkg.version;
}

function setPackageJsonVersion(newVersion) {
  const original = read(PACKAGE_JSON);
  const re = /("version"\s*:\s*")([^"]*)(")/;
  const m = original.match(re);
  if (!m) throw new Error(`Cannot find "version" in package.json`);
  if (m[2] === newVersion) return { from: m[2], to: newVersion, changed: false };
  write(PACKAGE_JSON, original.replace(re, `$1${newVersion}$3`));
  return { from: m[2], to: newVersion, changed: true };
}

const CARGO_VERSION_RE = /^(version\s*=\s*")([^"]*)(")/m;

function getCargoVersion() {
  const content = read(CARGO_TOML);
  const m = content.match(CARGO_VERSION_RE);
  if (!m) throw new Error(`Cannot find version in ${CARGO_TOML}`);
  return m[2];
}

function setCargoVersion(newVersion) {
  const original = read(CARGO_TOML);
  const m = original.match(CARGO_VERSION_RE);
  if (!m) throw new Error(`Cannot find version in ${CARGO_TOML}`);
  if (m[2] === newVersion) return { from: m[2], to: newVersion, changed: false };
  write(CARGO_TOML, original.replace(CARGO_VERSION_RE, `$1${newVersion}$3`));
  return { from: m[2], to: newVersion, changed: true };
}

function setPackageLockVersion(newVersion) {
  if (!fs.existsSync(PACKAGE_LOCK_JSON)) return { from: null, to: newVersion, changed: false };
  const original = read(PACKAGE_LOCK_JSON);
  // Update top-level "version" field (first occurrence after opening brace)
  const rootRe = /^(\{\s*"name"\s*:\s*"[^"]*"\s*,\s*"version"\s*:\s*")([^"]*)(")/m;
  // Update packages[""]."version" field
  const packagesRe = /("packages"\s*:\s*\{\s*""\s*:\s*\{\s*"name"\s*:\s*"[^"]*"\s*,\s*"version"\s*:\s*")([^"]*)(")/;

  let updated = original;
  let changed = false;

  const m1 = updated.match(rootRe);
  if (m1 && m1[2] !== newVersion) {
    updated = updated.replace(rootRe, `$1${newVersion}$3`);
    changed = true;
  }

  const m2 = updated.match(packagesRe);
  if (m2 && m2[2] !== newVersion) {
    updated = updated.replace(packagesRe, `$1${newVersion}$3`);
    changed = true;
  }

  if (changed) {
    write(PACKAGE_LOCK_JSON, updated);
    return { from: "(old)", to: newVersion, changed: true };
  }
  return { from: newVersion, to: newVersion, changed: false };
}

function usage() {
  console.log("Usage:");
  console.log("  node scripts/version.mjs set <x.y.z>   set version for Vue frontend & Rust backend");
  console.log("  node scripts/version.mjs check         verify versions are in sync");
}

async function main() {
  const [cmd, arg] = process.argv.slice(2);
  if (!cmd) {
    usage();
    process.exit(1);
  }

  if (cmd === "set") {
    if (!arg) {
      usage();
      process.exit(1);
    }
    if (!/^\d+\.\d+\.\d+$/.test(arg)) {
      console.error(`Invalid version: "${arg}" (expected x.y.z)`);
      process.exit(1);
    }
    const fe = setPackageJsonVersion(arg);
    const rust = setCargoVersion(arg);
    const lock = setPackageLockVersion(arg);
    if (fe.changed) console.log(`package.json: ${fe.from} -> ${fe.to}`);
    else console.log(`package.json: already ${fe.to}`);
    if (rust.changed) console.log(`src-tauri/Cargo.toml: ${rust.from} -> ${rust.to}`);
    else console.log(`src-tauri/Cargo.toml: already ${rust.to}`);
    if (lock.changed) console.log(`package-lock.json: ${lock.from} -> ${lock.to}`);
    else console.log(`package-lock.json: already ${lock.to}`);
    console.log(`\nVersion set to ${arg}. Restart Vite dev server if running! Don't forget to commit & tag v${arg}.`);
    return;
  }

  if (cmd === "check") {
    const feVersion = getPackageJsonVersion();
    const rustVersion = getCargoVersion();
    let ok = true;
    if (feVersion !== rustVersion) {
      console.error(`Version mismatch! frontend=${feVersion}, Rust=${rustVersion}`);
      ok = false;
    }
    if (fs.existsSync(PACKAGE_LOCK_JSON)) {
      const lock = JSON.parse(read(PACKAGE_LOCK_JSON));
      if (lock.version !== feVersion) {
        console.error(`Version mismatch! package.json=${feVersion}, package-lock.json=${lock.version}`);
        ok = false;
      }
    }
    if (!ok) {
      console.error(`Run: node scripts/version.mjs set <version>`);
      process.exit(1);
    }
    console.log(`Version OK (${feVersion}) — Vue frontend, Rust backend & lockfile in sync`);
    return;
  }

  usage();
  process.exit(1);
}

main().catch((err) => {
  console.error(err?.stack || String(err));
  process.exit(1);
});
