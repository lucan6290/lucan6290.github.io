param([Parameter(Mandatory)][string]$OutputDirectory)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$target = 'x86_64-pc-windows-msvc'
$desktop = Split-Path -Parent $PSScriptRoot
$temporary = Join-Path ([System.IO.Path]::GetTempPath()) ('luchuan-sign-' + [guid]::NewGuid())
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $OutputDirectory) { throw '输出目录必须尚未存在' }

Push-Location -LiteralPath $desktop
try {
    $null = New-Item -ItemType Directory -Path $temporary
    $config = Join-Path $temporary 'tauri.release.json'
    node scripts/windows-release.mjs config $config
    $version = (Get-Content -Raw -LiteralPath src-tauri/tauri.conf.json | ConvertFrom-Json).version
    if ($env:LUCHUAN_RELEASE_TAG -cne "desktop-v$version") { throw '桌面发布标签与版本不一致' }
    if ((Get-Content -Raw -LiteralPath package.json | ConvertFrom-Json).version -cne $version) { throw 'Tauri 与项目版本不一致' }
    node scripts/version.mjs check

    $thumbprint = $env:LUCHUAN_CODESIGN_THUMBPRINT.Trim()
    $certificate = Get-Item -LiteralPath "Cert:\CurrentUser\My\$thumbprint"
    if (-not $certificate.HasPrivateKey -or $certificate.NotBefore -gt (Get-Date) -or $certificate.NotAfter -lt (Get-Date) -or
        $certificate.EnhancedKeyUsageList.ObjectId -notcontains '1.3.6.1.5.5.7.3.3') { throw '签名证书需要有效的代码签名权限及可用私钥' }

    $signTool = $env:TAURI_WINDOWS_SIGNTOOL_PATH
    if (-not $signTool) {
        $sdk = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits/10/bin'
        $signTool = Get-ChildItem -LiteralPath $sdk -Directory | Where-Object Name -Match '^10\.\d+\.\d+\.\d+$' |
            Sort-Object { [version]$_.Name } -Descending | ForEach-Object { Join-Path $_.FullName 'x64/signtool.exe' } |
            Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    }
    if (-not $signTool -or -not (Test-Path -LiteralPath $signTool -PathType Leaf)) { throw '找不到 Windows SDK x64 SignTool' }
    $env:TAURI_WINDOWS_SIGNTOOL_PATH = $signTool
    $sevenZip = $env:LUCHUAN_7ZIP_PATH
    if (-not $sevenZip) {
        $sevenZip = (Get-Command 7z.exe -ErrorAction SilentlyContinue).Source
        if (-not $sevenZip) { $sevenZip = Join-Path $env:ProgramFiles '7-Zip/7z.exe' }
    }
    if (-not (Test-Path -LiteralPath $sevenZip -PathType Leaf)) { throw '找不到用于校验 NSIS 内部程序的 7-Zip' }

    node scripts/build-content-backend.mjs
    $backend = Get-Item -LiteralPath src-tauri/.bundle/dist/luchuan-content/luchuan-content.exe
    & $signTool sign /sha1 $thumbprint /fd SHA256 /tr $env:LUCHUAN_CODESIGN_TIMESTAMP_URL.Trim() /td SHA256 $backend.FullName
    & $backend.FullName --help

    node node_modules/@tauri-apps/cli/tauri.js build --ci --target $target --bundles nsis --config src-tauri/tauri.bundle.conf.json --config $config -- --locked

    $targetDirectory = "src-tauri/target/$target/release"
    $installers = @(Get-ChildItem -LiteralPath "$targetDirectory/bundle/nsis" -Filter "*_${version}_x64-setup.exe" -File)
    if ($installers.Count -ne 1) { throw '找不到唯一的 Windows x64 NSIS 安装包' }
    $installer = $installers[0]
    # Tauri 打包后还原未签名的本地程序，校验实际进入安装包的两份程序。
    & $sevenZip e -y "-o$temporary" $installer.FullName admin-desktop.exe luchuan-content.exe -r
    $app = Get-Item -LiteralPath (Join-Path $temporary 'admin-desktop.exe')
    $packagedBackend = Get-Item -LiteralPath (Join-Path $temporary 'luchuan-content.exe')
    foreach ($file in @($app, $packagedBackend, $installer)) {
        & $signTool verify /pa /all /tw $file.FullName
        $signature = Get-AuthenticodeSignature -LiteralPath $file.FullName
        if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Thumbprint -ne $thumbprint -or -not $signature.TimeStamperCertificate) {
            throw "文件签名、发布者或可信时间戳无效：$($file.Name)"
        }
    }

    $notes = Join-Path $temporary 'release-notes.md'
    $PSNativeCommandUseErrorActionPreference = $false
    $changelog = node scripts/extract-changelog.mjs "v$version" 2>$null
    if ($LASTEXITCODE -ne 0) { $changelog = "箓川码笺桌面端 $version" }
    $PSNativeCommandUseErrorActionPreference = $true
    $changelog | Set-Content -LiteralPath $notes -Encoding utf8NoBOM
    node scripts/windows-release.mjs stage $OutputDirectory $installer.FullName $notes
}
finally {
    Pop-Location
    if (Test-Path -LiteralPath $temporary) {
        # 只清理本次创建的目录内已知文件。
        foreach ($name in @('tauri.release.json', 'release-notes.md', 'admin-desktop.exe', 'luchuan-content.exe')) {
            $file = Join-Path $temporary $name
            if (Test-Path -LiteralPath $file) { Remove-Item -LiteralPath $file }
        }
        Remove-Item -LiteralPath $temporary
    }
}
