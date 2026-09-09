param(
  [string]$Python = ".venv\Scripts\python.exe",
  [string]$WorkerPython = ".venv-arm64\Scripts\python.exe",
  [string]$ModelPath = "data\models\person-segmentation.qdq.onnx"
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
if (-not [IO.Path]::IsPathRooted($Python)) { $Python = Join-Path $repo $Python }
& $Python -m pytest "$repo\tests"
if (-not [IO.Path]::IsPathRooted($WorkerPython)) { $WorkerPython = Join-Path $repo $WorkerPython }
& "$PSScriptRoot\doctor.ps1" -Python $WorkerPython -ModelPath $ModelPath -RequireNpu
& $WorkerPython "$repo\inference\worker.py" --provider qnn --require-npu --model $ModelPath
