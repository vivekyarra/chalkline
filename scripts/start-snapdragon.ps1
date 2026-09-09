param(
  [string]$Source = "camera:0",
  [string]$Python = ".venv\Scripts\python.exe",
  [string]$WorkerPython = ".venv-arm64\Scripts\python.exe",
  [string]$ModelPath = "data\models\person-segmentation.qdq.onnx",
  [switch]$Lan,
  [switch]$Demo
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
if (-not [IO.Path]::IsPathRooted($Python)) { $Python = Join-Path $repo $Python }
if (-not [IO.Path]::IsPathRooted($ModelPath)) { $ModelPath = Join-Path $repo $ModelPath }
if (-not [IO.Path]::IsPathRooted($WorkerPython)) { $WorkerPython = Join-Path $repo $WorkerPython }
$hostAddress = if ($Lan) { "0.0.0.0" } else { "127.0.0.1" }
if ($Demo) {
  & $Python -m chalkline.main --host $hostAddress --demo
} else {
  & $Python -m chalkline.main --host $hostAddress --source $Source --provider qnn --model $ModelPath --worker-python $WorkerPython
}
