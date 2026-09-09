# CHALKLINE technical proposal

## Product boundary

The MVP supports one fixed camera, one physical chalkboard, one teacher, and a short live lesson. The teacher uses a Snapdragon-powered HP PC. Students use ordinary browsers. Multi-camera tracking, transcription, translation, generative tutoring, and LMS integrations are outside the first release.

## Data path

The camera stream first passes through board calibration and perspective correction. A foreground segmentation model produces an occlusion mask. The board-state engine retains only previously observed pixels under occlusion, confirms candidate erasures across multiple unobstructed frames, and creates monotonically ordered changes against periodic checkpoints.

Each receiver obtains audio, board patches, and compact control messages. After a disconnect, the client requests a checkpoint plus subsequent changes. The browser shows freshness state when it cannot establish that a region is current.

## Snapdragon role

The proposed NPU task is foreground segmentation. A candidate is DeepLabV3-Plus-MobileNet from Qualcomm AI Hub, executed through the ONNX Runtime QNN provider. Image alignment, temporal change logic, encoding, and version bookkeeping remain on CPU for the MVP. This division must be confirmed on the entrant's exact Snapdragon X configuration, including operator support and proof that inference did not fall back from the NPU.

## Safety and fidelity rule

CHALKLINE preserves captured evidence. It never generates or reconstructs unobserved mathematical writing. Under uncertainty, it keeps the last verified state and labels the affected region stale or occluded.

## Initial bandwidth budget

The proposed average receiver budget is 24 kbps for audio, 32 kbps for board updates, and 8 kbps for application, encryption, and transport overhead. The sender may coalesce updates and delay nonessential checkpoints, but current audio and freshness signals have priority. The total and quality must be measured end to end before any 64 kbps performance claim is made.

## Main technical risk

The highest-risk error is treating temporary presenter occlusion as an erasure. The first defense is conservative erasure confirmation across multiple clear frames. The evaluation deliberately includes partial and full board occlusion followed by erasing.

