# CHALKLINE

**The board stays with you.**

CHALKLINE is a concept-stage teaching tool for live physical-blackboard lessons over constrained connections. A fixed USB camera feeds a Snapdragon-powered Windows PC, where local vision would separate presenter occlusion from board changes, preserve verified board pixels, and send versioned board patches with compressed audio to an ordinary student browser.

The goal is exact lesson continuity: keep the teacher's original handwriting readable, let a student return to an earlier board state, and recover the correct state after a connection drop. The system is explicitly designed to show stale or hidden regions rather than invent unseen writing.

## Proposed system

1. Select and rectify one fixed chalkboard on the teacher PC.
2. Run a candidate segmentation model on the Snapdragon NPU through ONNX Runtime QNN.
3. Track observed pixels, occlusion, confirmed erasures, and ordered board versions on CPU.
4. Deliver changed board regions, checkpoints, and compressed audio.
5. Rebuild the board in a lightweight browser with history and reconnect recovery.

The initial total target is **64 kbps per receiver, including transport**. This is a design target, not an achieved result.

## Proof plan

CHALKLINE will be compared with tuned low-frame-rate video and periodic snapshots plus audio under the same 64/128/256 kbps link profiles. The test lesson includes writing, presenter occlusion, erasing, a ten-second network interruption, and rejoining. Measurements cover blind symbol transcription, audio intelligibility, board-update delay, recovery correctness, total bytes, and verified CPU/NPU execution.

## Current status

This repository currently contains the technical proposal, evaluation protocol, and competition materials. The application, benchmark, pilot, and 64 kbps result have not been completed. Product imagery is AI-generated and labeled as concept imagery.

## Documents

- [Technical proposal](docs/TECHNICAL_PROPOSAL.md)
- [Evaluation protocol](docs/EVALUATION_PLAN.md)
- [Submission artifacts](submission/)

## Primary references

- [Qualcomm AI Hub: DeepLabV3-Plus-MobileNet](https://aihub.qualcomm.com/models/deeplabv3_plus_mobilenet)
- [ONNX Runtime: QNN Execution Provider](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html)
- [Microsoft Teams: camera-based board enhancement](https://support.microsoft.com/en-us/teams/meetings/share-whiteboards-and-documents-using-your-camera-in-microsoft-teams-meetings)
- [Microsoft Learn: Teams bandwidth guidance](https://learn.microsoft.com/en-us/microsoftteams/prepare-network)

## Author

Yarra Vivek — individual entry for the Snapdragon AI Lab Build & Present Challenge.

