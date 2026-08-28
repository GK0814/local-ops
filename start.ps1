[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [int]$PreferredPort,
    [switch]$Background
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $scriptDir

function Find-RunningConsoleUrl {
    foreach ($port in 9600..9609) {
        $url = "http://127.0.0.1:$port"
        try {
            $health = Invoke-RestMethod -Uri "$url/api/health" -TimeoutSec 1 -ErrorAction Stop
            if ($health.ok -eq $true -and $health.status -eq 'ok') {
                return $url
            }
        } catch {
            continue
        }
    }
    return $null
}

function Open-ConsoleUrl([string]$Url) {
    if (-not $NoBrowser) {
        Start-Process $Url
    }
}

function Show-StartupFailure([string]$Message) {
    if ($Background) {
        try {
            $shell = New-Object -ComObject WScript.Shell
            [void]$shell.Popup($Message, 0, '总控台启动失败', 16)
        } catch {
        }
    }
    throw $Message
}

$startupMutex = [System.Threading.Mutex]::new($false, 'Local\LocalOps.Console.Launcher')
$hasStartupMutex = $false
try {
    $hasStartupMutex = $startupMutex.WaitOne(0)
    if (-not $hasStartupMutex) {
        for ($attempt = 0; $attempt -lt 20; $attempt++) {
            Start-Sleep -Milliseconds 500
            $existingUrl = Find-RunningConsoleUrl
            if ($existingUrl) {
                Open-ConsoleUrl $existingUrl
                return
            }
        }
        Show-StartupFailure '另一个总控台启动操作仍未完成，请稍后重试。'
    }

    $existingUrl = Find-RunningConsoleUrl
    if ($existingUrl) {
        Open-ConsoleUrl $existingUrl
        return
    }

    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command python -ErrorAction SilentlyContinue
    }
    if (-not $python) {
        Show-StartupFailure '未找到 Python。请安装 Python 3.12+ 并将 python 加入 PATH。'
    }

    & $python.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"
    if ($LASTEXITCODE -ne 0) {
        Show-StartupFailure '总控台需要 Python 3.12 或更高版本。'
    }

    $arguments = @('server.py')
    if ($PreferredPort) {
        $arguments += @('--preferred-port', $PreferredPort)
    }
    if ($Background) {
        $arguments += '--no-browser'
        $process = Start-Process -FilePath $python.Source -ArgumentList $arguments `
            -WorkingDirectory $scriptDir -WindowStyle Hidden -PassThru
        for ($attempt = 0; $attempt -lt 24; $attempt++) {
            Start-Sleep -Milliseconds 500
            $startedUrl = Find-RunningConsoleUrl
            if ($startedUrl) {
                Open-ConsoleUrl $startedUrl
                return
            }
            if ($process.HasExited) {
                break
            }
        }
        Show-StartupFailure '总控台未能在 12 秒内完成启动。请双击 start.bat 查看详细错误。'
    }

    if ($NoBrowser) {
        $arguments += '--no-browser'
    }
    & $python.Source @arguments
} finally {
    if ($hasStartupMutex) {
        $startupMutex.ReleaseMutex()
    }
    $startupMutex.Dispose()
}
