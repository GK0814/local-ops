[CmdletBinding()]
param(
    [string]$DesktopPath = [Environment]::GetFolderPath('Desktop')
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'start.ps1') -PathType Leaf)) {
    throw '未找到总控台启动脚本。请在完整的总控台项目目录中运行此脚本。'
}
if (-not (Test-Path -LiteralPath $DesktopPath -PathType Container)) {
    throw "桌面目录不可用：$DesktopPath"
}

$shortcutPath = Join-Path $DesktopPath '总控台.lnk'
$powershell = Join-Path $PSHOME 'powershell.exe'
$arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" -Background' -f
    (Join-Path $projectRoot 'start.ps1').Replace('"', '`"')
$iconPath = Join-Path $projectRoot 'static\assets\favicon.ico'

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $powershell
$shortcut.Arguments = $arguments
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = '打开或启动本机总控台'
if (Test-Path -LiteralPath $iconPath -PathType Leaf) {
    $shortcut.IconLocation = "$iconPath,0"
}
$shortcut.Save()

Write-Output "已创建桌面快捷方式：$shortcutPath"
