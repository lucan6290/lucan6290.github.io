# XLucan Admin Desktop

[中文](../README.md)

The desktop app uses Tauri and Vue with a local Python content service. Open a workspace to edit the Markdown and images in `frontend/content/`, preview the reader site, and manage publishing from the workspace.

## Development

Use Node.js 22+, Python 3.10+, Rust stable, WebView2 and the MSVC build tools. From the repository root:

```powershell
cd admin-desktop
npm install
python -m venv src-backend/.venv
src-backend/.venv/Scripts/python.exe -m pip install -r src-backend/requirements.txt
npm run tauri:dev
```

Tauri prefers `127.0.0.1:18000` and uses an OS-assigned loopback port if it is unavailable. The development UI uses `127.0.0.1:14200`. See the [desktop guide](../README.md) for browser-only development and test commands.

## Windows installer

The Windows x64 NSIS installer includes the content service and Python runtime. Follow the [Windows release guide](Windows%20发布与更新.md) to build, sign, and verify the installer. On first launch, choose the blog repository root or its `frontend/content/` directory.

The [documentation index](DOCUMENTATION_INDEX.md) links to the content API contract, workspace switching, preview builds, and release details.
