# Snapdragon setup

CHALKLINE targets a Snapdragon-powered HP PC running Windows 11. It uses a Windows host process for camera/OpenCV work and a separate native ARM64 Python process for strict QNN/HTP inference.

## Prerequisites

- Current Windows, firmware, Qualcomm NPU driver, and camera permissions.
- Python 3.11 host installation and native ARM64 Python 3.11 installation. Confirm each interpreter with `python -c "import platform; print(platform.machine())"`.
- Git and a Chromium browser.
- A QNN-compatible, fixed-shape, quantized DeepLabV3-Plus-MobileNet ONNX model placed at `data\models\person-segmentation.qdq.onnx`.

The model manifest is [inference/model_manifest.json](../inference/model_manifest.json). Update its SHA-256 after obtaining the artifact from Qualcomm AI Hub. Do not use an unverified file or a dynamically shaped float model for strict HTP execution.

Inspect and fetch the available Qualcomm artifact with the official models CLI:

```powershell
python -m pip install qai-hub-models-cli
qai-hub-models info deeplabv3_plus_mobilenet
qai-hub-models fetch deeplabv3_plus_mobilenet --runtime onnx --precision w8a16
```

Confirm that the selected artifact matches the installed QNN/ONNX Runtime combination. Copy its ONNX file to the expected path and record its hash in the manifest.

## Install

From PowerShell in the repository root:

```powershell
.\scripts\setup-snapdragon.ps1 `
  -ArmPython 'C:\path\to\native-arm64\python.exe' `
  -HostPython 'C:\path\to\host\python.exe'
```

The setup creates `.venv` for the application and `.venv-arm64` for QNN inference. It fails if the NPU interpreter is not ARM64.

## Validate and run

```powershell
.\scripts\doctor.ps1 -Python '.venv-arm64\Scripts\python.exe' -RequireNpu
.\scripts\verify.ps1
.\scripts\start-snapdragon.ps1 -Source 'camera:0' -Lan
```

Open `http://localhost:8000/teacher` on the teacher PC. The student opens `http://<teacher-ip>:8000/`. Allow the selected network scope through Windows Firewall when using `-Lan`.

`start-snapdragon.ps1` uses strict QNN mode. Failure to create the HTP session stops the source pipeline and appears in the teacher console. It does not fall back to CPU.

Measure the same artifact through both native ARM64 providers:

```powershell
.venv-arm64\Scripts\python.exe scripts\benchmark_inference.py --model data\models\person-segmentation.qdq.onnx --provider cpu --output evidence\snapdragon-cpu\inference.json
.venv-arm64\Scripts\python.exe scripts\benchmark_inference.py --model data\models\person-segmentation.qdq.onnx --provider qnn --output evidence\snapdragon-qnn\inference.json
```

For a clearly labeled protocol/UI fixture without inference or a camera:

```powershell
.\scripts\start-snapdragon.ps1 -Demo
```

The fixture is for troubleshooting and is not evidence of camera or NPU execution.
