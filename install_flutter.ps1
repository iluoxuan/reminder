# 检查是否以管理员权限运行
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "请以管理员权限运行此脚本！"
    Break
}

# 创建目录
Write-Host "创建 Flutter 目录..."
New-Item -ItemType Directory -Force -Path "C:\src"

# 下载 Flutter SDK
Write-Host "正在下载 Flutter SDK..."
$flutterUrl = "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.19.3-stable.zip"
$flutterZip = "C:\src\flutter.zip"
Invoke-WebRequest -Uri $flutterUrl -OutFile $flutterZip

# 解压 Flutter
Write-Host "正在解压 Flutter SDK..."
Expand-Archive -Path $flutterZip -DestinationPath "C:\src" -Force

# 删除 zip 文件
Remove-Item $flutterZip

# 设置环境变量
Write-Host "设置环境变量..."
$flutterPath = "C:\src\flutter\bin"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -notlike "*$flutterPath*") {
    $newPath = $currentPath + ";$flutterPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Flutter 已添加到环境变量中"
} else {
    Write-Host "Flutter 已经在环境变量中"
}

# 下载并安装 VS Code
Write-Host "正在下载 VS Code..."
$vscodeUrl = "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user"
$vscodeInstaller = "C:\src\vscode-installer.exe"
Invoke-WebRequest -Uri $vscodeUrl -OutFile $vscodeInstaller

# 安装 VS Code
Write-Host "正在安装 VS Code..."
Start-Process -FilePath $vscodeInstaller -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-" -Wait

# 删除安装程序
Remove-Item $vscodeInstaller

# 运行 flutter doctor
Write-Host "正在检查 Flutter 环境..."
& "C:\src\flutter\bin\flutter.bat" doctor

Write-Host "安装完成！请重启电脑以使环境变量生效。"
Write-Host "重启后，请运行 'flutter doctor' 检查是否还有需要解决的问题。"
Write-Host "安装完成后，请在 VS Code 中安装 Flutter 和 Dart 插件。" 