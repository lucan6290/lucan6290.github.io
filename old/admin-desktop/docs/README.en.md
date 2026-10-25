# XLucan Admin Desktop (admin-desktop)

> [中文版本](../README.md) | English

The desktop management application for the XLucan (xiaocancoding) personal tech site and knowledge base. Built with Tauri 2 + Vue 3, it provides article writing, editing, image management, category/tag maintenance, preview builds, and other writing-assistance capabilities.

## Features

- Article management and editing (ByteMD rich text + Front Matter)
- Media / image management
- Category / tag maintenance (Registry)
- Preview builds
- AI writing assistance
- Dashboard and settings

## Tech Stack

- Frontend: Vue 3, Vite, TypeScript, Pinia, ByteMD
- Desktop: Tauri 2 (Rust)
- Packaging: NSIS / MSI

## Getting Started

### Prerequisites

- Node.js 22+
- Rust (stable)
- Tauri system dependencies (Windows: WebView2, MSVC build tools)

### Installation and Running

```bash
npm install
npm run tauri:dev   # local development (frontend port 14200)
```

## Development

### Build

```bash
npm run build           # frontend type check + build
npm run tauri:build     # package installers (NSIS / MSI)
```

### Quality Checks

```bash
npm run build           # vue-tsc type check + vite build
```

## Project Structure

```
admin-desktop/
├── src/               # Vue frontend source
├── src-tauri/         # Tauri / Rust backend
├── src-backend/       # local Python backend (dev helper)
├── scripts/           # version / changelog scripts
└── docs/              # English docs
```

## FAQ

- Build failure: make sure WebView2 and Visual Studio C++ build tools are installed
- Auto-update: requires signing keys to be configured

## Contributing and Security

- Contributing Guide: [`CONTRIBUTING.md`](../CONTRIBUTING.md)
- Code of Conduct: [`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md)
- Security Policy: [`SECURITY.md`](../SECURITY.md)

## License

GPL-3.0 — see [`LICENSE`](../LICENSE).
