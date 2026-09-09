param(
  [Parameter(Mandatory=$true)][string]$ArmPython,
  [Parameter(Mandatory=$true)][string]$HostPython,
  [string]$ModelPath = "data\models\person-segmentation.qdq.onnx"
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$arch = & $ArmPython -c "import platform; print(platform.machine())"
if ($arch.Trim().ToUpperInvariant() -notin @("ARM64", "AARCH64")) {
  throw "ArmPython must be native ARM64. Detected: $arch"
}
& $HostPython -m venv "$repo\.venv"
$hostExe = "$repo\.venv\Scripts\python.exe"
& $hostExe -m pip install --upgrade pip
& $hostExe -m pip install -e "$repo[test]"
& $ArmPython -m venv "$repo\.venv-arm64"
$armExe = "$repo\.venv-arm64\Scripts\python.exe"
& $armExe -m pip install --upgrade pip
& $armExe -m pip install numpy==1.26.4 onnxruntime-qnn==2.0.0
if (-not (Test-Path "$repo\$ModelPath")) {
  Write-Warning "QDQ model is missing at $ModelPath. Export/download the Qualcomm AI Hub artifact described in inference/model_manifest.json."
}
& "$PSScriptRoot\doctor.ps1" -Python $armExe -ModelPath "$repo\$ModelPath"
