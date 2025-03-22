# 设置 Flutter 环境变量
$flutterPath = "C:\src\flutter\bin"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -notlike "*$flutterPath*") {
    $newPath = $currentPath + ";$flutterPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Flutter 已添加到环境变量中"
} else {
    Write-Host "Flutter 已经在环境变量中"
}

# 运行 flutter doctor 检查环境
Write-Host "正在检查 Flutter 环境..."
& "C:\src\flutter\bin\flutter.bat" doctor 