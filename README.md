# CHALKLINE

**The board stays with you.**

CHALKLINE is a runnable MVP for live physical-chalkboard lessons over constrained connections. A fixed USB camera feeds a Snapdragon-powered HP Windows PC, where local vision separates presenter occlusion from board changes, preserves verified board pixels, and sends versioned board patches with browser audio to an ordinary student browser.

The goal is exact lesson continuity: keep the teacher's original handwriting readable, let a student return to an earlier board state, and recover the correct state after a connection drop. The system is explicitly designed to show stale or hidden regions rather than invent unseen writing.

## MVP system

1. Select and rectify one fixed chalkboard on the teacher PC.
2. Run strict presenter segmentation on the Snapdragon NPU through ONNX Runtime QNN, with CPU fallback disabled.
3. Track observed pixels, occlusion, confirmed erasures, and ordered board versions on CPU.
4. Deliver changed board regions, checkpoints, and compressed audio.
5. Rebuild the board in a lightweight browser with history and reconnect recovery.

The initial total target is **64 kbps per receiver, including transport**. This remains a design target until the controlled wire-level benchmark is complete.

## Proof plan

CHALKLINE will be compared with tuned low-frame-rate video and periodic snapshots plus audio under the same 64/128/256 kbps link profiles. The test lesson includes writing, presenter occlusion, erasing, a ten-second network interruption, and rejoining. Measurements cover blind symbol transcription, audio intelligibility, board-update delay, recovery correctness, total bytes, and verified CPU/NPU execution.

## Run on Snapdragon

Use Windows PowerShell on a Snapdragon-powered HP PC:

```powershell
.\scripts\setup-snapdragon.ps1 `
  -ArmPython 'C:\path\to\native-arm64\python.exe' `
  -HostPython 'C:\path\to\host\python.exe'
.\scripts\verify.ps1
.\scripts\start-snapdragon.ps1 -Source 'camera:0' -Lan
```

Open `http://localhost:8000/teacher` and give students `http://<teacher-ip>:8000/`. See [Snapdragon setup](docs/SETUP_SNAPDRAGON.md) for the model artifact, native QNN worker, and verification requirements.

## Evidence status

The core application and automated invariant tests are implemented. Physical camera-to-browser evidence, the same-device CPU/NPU comparison, the wire-level benchmark, screenshots, and demo recording must be captured on the target Snapdragon system before those results are claimed. The 64 kbps figure remains unverified. Product imagery in `submission/` remains labeled concept imagery.

## Documents

- [Technical proposal](docs/TECHNICAL_PROPOSAL.md)
- [Evaluation protocol](docs/EVALUATION_PLAN.md)
- [Build status](docs/BUILD_STATUS.md)
- [Snapdragon setup](docs/SETUP_SNAPDRAGON.md)
- [Protocol](docs/PROTOCOL.md)
- [Benchmark protocol](docs/BENCHMARK.md)
- [Inference disclosure](docs/INFERENCE_DISCLOSURE.md)
- [Demo recording script](docs/DEMO_SCRIPT.md)
- [Submission artifacts](submission/)

## Primary references

- [Qualcomm AI Hub: DeepLabV3-Plus-MobileNet](https://aihub.qualcomm.com/models/deeplabv3_plus_mobilenet)
- [ONNX Runtime: QNN Execution Provider](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html)
- [Microsoft Teams: camera-based board enhancement](https://support.microsoft.com/en-us/teams/meetings/share-whiteboards-and-documents-using-your-camera-in-microsoft-teams-meetings)
- [Microsoft Learn: Teams bandwidth guidance](https://learn.microsoft.com/en-us/microsoftteams/prepare-network)

## Author

Yarra Vivek — individual entry for the Snapdragon AI Lab Build & Present Challenge.
