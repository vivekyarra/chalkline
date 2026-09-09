# Inference disclosure

| Component | Intended execution | Fallback behavior | Verification state |
|---|---|---|---|
| DeepLabV3-Plus-MobileNet presenter segmentation | Snapdragon NPU through native ARM64 ONNX Runtime QNN HTP | Disabled in strict mode | Pending target run and provider profile |
| Camera decode and perspective rectification | CPU | None | Implemented; physical run pending |
| Temporal change and erasure logic | CPU | None | Automated invariant tests implemented |
| Patch encoding and version storage | CPU | None | Automated tests implemented |
| Student reconstruction and history | Browser CPU/GPU canvas | None | Implemented; browser recording pending |
| Audio | Browser WebRTC/Opus | No cloud relay | Implemented; two-device run pending |

The application does not claim that every component runs on the NPU. A provider name alone is insufficient evidence. A valid NPU evidence bundle includes exact device and software versions, native process architecture, model hash, strict CPU-fallback-disabled session settings, successful output, and QNN profiling tied to the run.
