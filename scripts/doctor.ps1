param(
  [string]$Python = ".venv-arm64\Scripts\python.exe",
  [string]$ModelPath = "data\models\person-segmentation.qdq.onnx",
  [switch]$RequireNpu
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
if (-not [IO.Path]::IsPathRooted($Python)) { $Python = Join-Path $repo $Python }
if (-not [IO.Path]::IsPathRooted($ModelPath)) { $ModelPath = Join-Path $repo $ModelPath }
if (-not (Test-Path $Python)) { throw "Python not found: $Python" }
$info = & $Python -c "import json,platform,sys; print(json.dumps({'machine':platform.machine(),'python':sys.version,'executable':sys.executable}))"
$parsed = $info | ConvertFrom-Json
if ($parsed.machine.ToUpperInvariant() -notin @("ARM64", "AARCH64")) { throw "Native ARM64 Python required; detected $($parsed.machine)" }
Write-Host "ARM64 Python: OK"
& $Python -c "import numpy,onnxruntime; print('ARM64 inference packages: OK')"
if (-not (Test-Path $ModelPath)) { throw "Model not found: $ModelPath" }
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ModelPath).Hash.ToLowerInvariant()
Write-Host "Model SHA-256: $hash"
if ($RequireNpu) {
  & $Python -c "import onnxruntime as ort; p=ort.get_available_providers(); print(p); assert 'QNNExecutionProvider' in p, 'QNNExecutionProvider unavailable'"
  Write-Host "QNN provider registration: OK (strict model execution is verified by verify.ps1)"
}
