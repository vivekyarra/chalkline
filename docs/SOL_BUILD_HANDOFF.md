# CHALKLINE: executable build plan for GPT-5.6 Sol

Prepared 9 September 2026. This is an implementation handoff, not a claim that implementation or hardware validation has happened.

## 1. Read this first

Build a real fixed-camera chalkboard broadcaster **on and for Snapdragon-powered HP Windows PCs**. The student needs only a browser. All installation, implementation, runtime validation, and CPU/NPU comparisons in this plan target that Snapdragon laptop. Keep product copy, repository documentation, and the demo focused on this platform. Describe measured execution only after it is verified.

The requested outcome is a convincing camera-to-browser MVP, with preserved handwriting, conservative occlusion handling, confirmed erasures, history, reconnect recovery, audio, reproducible comparisons, and inspectable NPU evidence. Do not spend the build on another proposal, landing page, elaborate dashboard, or cloud integration. Do not submit the competition entry.

### Verified competition context

The [Unstop Solution Submission Round](https://unstop.com/competitions/crp-snapdragon-ai-lab-build-present-challenge-qualcomm-1748893/amp), checked on 9 September, accepts solutions designed, developed, or intended for optimization on Snapdragon-powered HP PCs. It lists technical implementation, use case/innovation, deployment/accessibility, and presentation/documentation as evaluation criteria. It allows one individual submission and says a properly submitted entry cannot be changed. The publicly listed registration deadline is 30 September 2026, 11:59 PM IST; recheck the authenticated submission deadline before release. Proposal eligibility is distinct from our stronger product-readiness goal. Internship opportunity is subject to eligibility, not guaranteed by a build or award.

### Starting state verified locally

- `D:\CHALKLINE\repository` contains README, technical proposal, evaluation protocol, license, and submission assets; no application exists.
- That directory currently has no Git checkout metadata. README identifies `https://github.com/vivekyarra/chalkline`.
- Existing claims correctly label 64 kbps as a target and generated images as concept imagery.
- Preserve the proposal and assets. Update their status only when evidence supports it.

### Operating instructions for Sol

Work in the phase order below. Complete each available phase, verify its gate, record results, and continue without asking permission between routine phases. Stop only the work that requires missing hardware, credentials, physical camera access, or user action; continue independent work. Do not use subagents unless requested. Do not install cloud infrastructure or publish the entry. Never replace measurements with estimates in a results table.

Keep `docs/BUILD_STATUS.md` with phase, changed files, commands, observed result, next exact command, and external blockers. Use it to resume after context resets. Read this document once, then the current phase and relevant code. Avoid repeated whole-repository audits and repeated full test suites without a change that justifies them.

## 2. Freeze the scope and architecture

### Supported scenario

One fixed USB/web camera, one dark chalkboard, one presenter, one lesson, and one student receiver for the measured MVP. Default capture 1280x720; processing target 8 FPS; canonical board width 1024 with height derived from calibration. These are starting configuration values, not measured capability. Preserve small symbols over smooth motion. Mount the camera; keep lighting stable; require a briefly unobstructed initial board. A second student is a smoke test, not a scaling claim.

No OCR, handwriting regeneration, LLM, inpainting, automatic camera tracking, translation, account system, LMS, native student app, or production internet relay. Local inference must work after model installation with internet disconnected. LAN is sufficient for the working demo; the constrained-network experiment must be labeled separately.

### Chosen stack

| Component | Implementation decision |
|---|---|
| Capture, rectification, state engine | Python 3.11 x64, OpenCV, NumPy |
| Local HTTP/WebSocket service | FastAPI + Uvicorn, SQLite, local filesystem |
| Student and teacher UI | Vite + TypeScript + ordinary HTML/CSS/Canvas; no UI framework required |
| Snapdragon CPU comparison | Native ARM64 ONNX Runtime CPU in a separate worker process |
| Target inference | Native ARM64 Python worker, NumPy and a pinned compatible ONNX Runtime/QNN package combination |
| Audio | Browser-to-browser WebRTC audio; local service relays signaling only |
| Patches | Lossless PNG tile replacements over binary WebSocket messages |
| Tests | pytest for engine/protocol, Playwright for browser flows |
| Evidence | JSONL, CSV, PNG, real screen recording; FFmpeg where needed |

**Deliberate portability boundary:** keep the main Python/OpenCV application x64 initially, including under Windows emulation on Snapdragon. Run the inference worker as a separate native ARM64 process. This avoids making native ARM64 OpenCV availability a prerequisite. Disclose the emulated host in all hardware results. Native migration of the host is optional only after the complete MVP works. Do not attempt to load ARM64 DLLs into x64 Python.

Do not install similarly named ORT packages into the same environment without checking their release instructions. QNN packaging has changed; lock a tested coherent set, not whatever an unqualified latest install produces. No source-building a giant dependency tree as the default route.

### Data flow

USB camera -> frame ID/time -> model preprocessing -> segmentation worker -> matching mask -> perspective rectification -> conservative board-state engine -> durable version -> patches/checkpoint -> student Canvas.

Teacher browser microphone -> WebRTC Opus audio -> student browser. Signaling passes through FastAPI. Camera imagery stays on the teacher laptop except reconstructed board pixels; raw video leaves only in the explicitly selected benchmark baseline. Teacher preview is localhost-only.

### Planned repository layout

```text
app/chalkline/
  main.py                 # HTTP, WS, lifecycle
  capture.py              # camera and real-time file replay
  calibration.py          # points, validation, homography
  pipeline.py             # bounded queues, matching IDs, timings
  segmentation_client.py  # worker lifecycle and binary IPC
  board_state.py          # pixel trust, stability, visibility
  change_detection.py     # addition/erasure decisions
  patches.py              # protocol and encoding
  store.py                # SQLite event log and checkpoints
  telemetry.py            # counters and structured logs
inference/worker.py        # same IPC contract, CPU or strict QNN
inference/model_manifest.json
web/src/{teacher,student,protocol,board,audio,history}.ts
scripts/{setup-snapdragon,doctor,start-snapdragon,verify}.ps1
scripts/{fetch_model,prepare_model,make_fixture,run_benchmark,report_results}.py
tests/{unit,integration,browser}/
bench/{profiles,ground_truth,configs}/
docs/{BUILD_STATUS,SETUP_SNAPDRAGON,PROTOCOL,BENCHMARK,INFERENCE_DISCLOSURE,DEMO_SCRIPT,RESULTS}.md
evidence/<run-id>/{manifest.json,events.jsonl,metrics.csv,screenshots/,profiles/}
```

These files and commands are targets to implement; they do not exist yet. Keep large recordings, model binaries, runtime libraries, and personal footage out of normal Git commits. Track their provenance, hashes, retrieval instructions, and permitted distribution method.

## 3. Phase 0 — prepare a safe working checkout (30–45 minutes planning allowance)

1. Read any applicable AGENTS.md, the three existing Markdown documents, and license. Inspect the actual repository remote read-only.
2. Since `repository` is an exported folder, clone the existing remote into `D:\CHALKLINE\worktree` if possible. Compare existing proposal files before copying this handoff and missing local artifacts into it. Do not initialize a new unrelated history over the export or overwrite a remote checkout. If access fails, work locally and record that publication is pending.
3. Inspect available Python, Node, Git, camera, FFmpeg, and OS architecture. Use explicit interpreter paths in scripts. Record process architecture separately from OS architecture. Never infer Snapdragon from a model name in a config.
4. On the Snapdragon PC, create isolated host and model-preparation environments, plus the native ARM64 inference environment. Resolve and lock dependencies. Use `npm.cmd` on PowerShell when necessary. Model preparation may use x64 Python under Windows emulation on this same Snapdragon PC.
5. Create `BUILD_STATUS.md`, an ignored data directory, and run directories. Runtime logs must exclude credentials and private full paths where exported publicly.

**Gate:** one command starts a health endpoint and serves an empty student shell; `doctor` prints truthful hardware/runtime status. Nothing claims NPU availability here.

## 4. Phase 1 — remove model and target-runtime uncertainty early

Do this before spending a day on UI. Allow roughly two focused hours for the first usable CPU mask and reproducible model artifact; this is a timebox for a decision, not a completion guarantee.

1. Start with [Qualcomm DeepLabV3-Plus-MobileNet](https://aihub.qualcomm.com/models/deeplabv3_plus_mobilenet). Its catalog describes VOC2012, 21 classes, and 513x513 input. Verify the actual downloaded/exported artifact rather than assuming those details apply to every export.
2. Read the [model implementation](https://github.com/qualcomm/ai-hub-models/blob/main/src/qai_hub_models/models/deeplabv3_plus_mobilenet/model.py) and export instructions. Obtain a reproducible float ONNX model and a QNN-compatible quantized ONNX artifact, or prepare the latter using representative calibration frames. Avoid making remote AI Hub jobs a runtime requirement. If an export requires account access, isolate that blocker and use the documented local source/export path where supported.
3. Freeze a manifest: origin URL, source revision, license and weight terms, SHA-256, input names/shapes/dtype, RGB/BGR order, resize/letterbox rule, normalization, output layout, class mapping, precision, exporter version, and quantization calibration-set hash. Confirm person class from metadata/source; do not blindly hardcode a class index.
4. Test on 20–30 real presenter frames: front, side, raised arm, hand near chalk, dark clothing, partial body, standing still, and no presenter. Save original, mask overlay, inference timing. A simulated rectangle is acceptable only for engine tests, never as presenter-model proof.
5. Prepare a disjoint calibration set of roughly 100–300 representative frames if quantizing. Keep evaluation frames separate. Compare float/quantized mask quality; do not calibrate with random tensors and call the model validated.
6. Build one native ARM64 worker with `--provider cpu` and `--provider qnn --require-npu` on the Snapdragon PC. An incompatible process architecture or missing NPU runtime must produce a clear reason and nonzero exit. A provider failure must not silently switch to CPU.

### Worker interface, implement literally

- Persistent child process; stdin/stdout in binary mode; stderr for logs only.
- Frame message: little-endian uint32 header byte length, UTF-8 JSON header, then exactly `payload_bytes` of contiguous preprocessed tensor bytes.
- Header includes protocol version, request ID, capture timestamp, shape, dtype, and byte count. Enforce explicit size/shape limits; no pickle or arbitrary object loading.
- Response uses the same framing: matching request ID, success/error, model hash, inference duration, reported backend, mask shape, and one uint8 per mask pixel. Never write debug prints into stdout.
- Keep at most one inference request running and one newest pending camera frame. If overloaded, replace the pending frame, count the drop, and process the matching image/mask together. Never apply a previous mask to a new image.
- On timeout/crash, freeze board commits, mark inference unavailable, and restart the worker once with a bounded timeout. Repeated failure leaves a visible error; it does not fabricate clear masks.

For current setup syntax, use the [versioned QNN project documentation](https://github.com/onnxruntime/onnxruntime-qnn/blob/main/docs/execution_providers/QNN-ExecutionProvider.md). It distinguishes newer standalone QNN releases from older integration instructions. Resolve the package/runtime compatibility and provider registration for the exact pinned release. Keep inference native ARM64 on the target; model preparation can happen on x64. Record package, runtime, driver, and backend versions separately.

**Gate:** a real model produces usable person masks on the Snapdragon PC, files/hashes are pinned, IPC is tested, and strict QNN executes successfully with traceable evidence. Run the runtime smoke test from Phase 7 here; reserve the full performance experiment for the complete pipeline. If this model fails quality or export, investigate one small human-segmentation alternative from Qualcomm/open-source; record the reason and retain the same worker contract. Do not spend the whole build browsing models.

## 5. Phase 2 — camera, calibration, and first live browser pixels

1. Implement camera enumeration, explicit device index, requested/actual resolution reporting, capture timestamp, and clean shutdown. Support `--source camera:0` and `--source file:<path>`; file mode must pace by source timestamps and visibly say Replay.
2. Teacher page at `http://localhost:8000/teacher`: raw preview and four draggable points ordered top-left, top-right, bottom-right, bottom-left. Reject crossed, degenerate, tiny, or out-of-frame quadrilaterals. Show rectified preview before Save.
3. Save source dimensions, camera identity, points, output size, and homography with calibration ID. Revalidate on restart or resolution change. Keep a Recalibrate action. Camera movement invalidates fidelity: include a manual pause and a conservative alignment-change detector using visible board edges/features; pause on uncertain alignment instead of smearing the stored board.
4. Segment the source camera frame, then rectify its person mask with the same homography using nearest-neighbor sampling. Rectify board RGB separately. Account for model letterboxing when mapping the mask back.
5. Send an initial lossless board checkpoint to a student Canvas. Confirm on another browser/device on the LAN. Bind localhost by default and offer explicit `--lan`; grant only necessary firewall access. Teacher mutation routes stay local or require a session token; possession of the student link does not grant calibration controls.

**Gate:** a real handwritten equation is readable in the student browser, with camera and rectified views available on the teacher page. Screenshot both. A fixture-only pass is recorded separately if a physical board is unavailable.

## 6. Phase 3 — board truth, occlusion, changes, and erasures

Implement state at pixel level first; tiles are a transport optimization. Each pixel has committed RGB, observed/unknown flag, visibility status, last observed time, and candidate stability state. Preserve never-seen regions as unknown, not as a guessed clean board.

### Processing rules

1. Expand the person mask conservatively (initial 5–9 pixels at canonical scale, tune on hands). Combine it with transient motion/uncertainty around the presenter. Add a short mask-release hold, initially 300 ms. A stationary presenter must remain masked by the real model; motion alone is insufficient.
2. Under occlusion: retain last committed pixels. Set a separate stale/occluded overlay. Do not burn overlays into stored board images. Unknown pixels remain visibly unknown.
3. On a clear region: compare against the committed board after a conservative global brightness-change check. If much of the board changes simultaneously without credible writing structure, freeze and flag lighting/alignment uncertainty.
4. Generate candidates using robust color/luminance difference plus local stroke contrast. Initial difference threshold 12/255 and three clear observations spanning at least 350 ms. These are tunable defaults; log them and freeze before final evaluation.
5. Confirm changes only from stable clear observations. Candidate state resets when occluded or unstable. Frame drops cannot substitute for observations.
6. Treat a reduction in local chalk-stroke evidence as a candidate erasure. Require a longer clear interval, initially five observations over at least 750 ms. Partial erasures update only verified clear pixels. Record a labeled erasure event for history navigation; do not erase a whole tile because one part changed.
7. Commit actual captured pixel values from stable observations. Do not smooth away superscripts, replace handwriting with OCR, or synthesize hidden writing. Rewriting over an old symbol becomes a verified pixel replacement, even if semantic addition/erasure classification is ambiguous.
8. Reset candidate buffers on capture discontinuity, calibration change, and session restart. Any calibration change starts a new board epoch.

### Essential tests and recorded physical checks

- Stationary board/noise: no continuous patch storm after settling.
- Person walks across existing writing, then stands still: writing is retained; mask/age says stale; no false erase event.
- Writing occurs behind a person: old/unknown state remains until revealed, then new writing appears.
- Erase one symbol while hand obscures it: change commits only after clear confirmation.
- Erase half the board, then all: clear regions update correctly without losing unrelated writing.
- Lighting jump, camera bump, missed inference, raised hand, glare: uncertainty freezes unsafe commits and is visible.

**Gate:** recorded scripted clip and unit fixtures both establish the above invariants. Prefer delayed updates to false erasures. Publish remaining failure cases, particularly undetected hands and shadows; semantic person segmentation does not guarantee every occluder is detected.

## 7. Phase 4 — durable patches, history, and recovery

### Protocol v1

Use lossless 64x64 tile replacement PNGs initially. Group all tiles in one committed board version into one atomic transaction. Do not use JPEG for protocol correctness tests. Each transaction header includes:

```json
{
  "protocol": 1, "session_id": "uuid", "epoch": "uuid",
  "base_version": 41, "version": 42, "kind": "patch",
  "capture_ms": 123456, "committed_ms": 123900,
  "tiles": [{"x": 0, "y": 64, "w": 64, "h": 64,
             "offset": 0, "length": 1234, "sha256": "..."}]
}
```

The integers above illustrate schema, not results. Binary message framing is uint32 JSON length + JSON + concatenated PNG payloads. Validate lengths, coordinates, hashes, version bounds, and total allocation before decode. Include dimensions, validity/unknown mask, freshness metadata, and calibration ID in checkpoints. Freshness has its own ordered revision and board-version reference so a motion-only update does not require PNG data.

### Atomicity and state machine

1. Create durable image blobs using temporary files and atomic rename. Then commit the version metadata to SQLite in a transaction. Only publish committed versions. On restart, ignore/clean orphan blobs and rebuild from the last complete checkpoint/log.
2. Browser states: CONNECTING -> SYNCING -> LIVE; DISCONNECTED and HISTORY are explicit. Maintain a live backing canvas separately from the viewed historical canvas.
3. Apply a patch only when session/epoch matches and `base_version == local_version`. Decode all tiles before drawing to a staging canvas; swap atomically and acknowledge after application. Ignore exact duplicates; gap, corruption, or incompatible epoch triggers resync.
4. Checkpoints: initial, then locally every 30 versions or 30 seconds, whichever comes first. Do not broadcast a full checkpoint to all receivers on that schedule; send it on join/resync when needed.
5. Reconnect request includes epoch and last applied version. If retained deltas form a contiguous chain, send them. Otherwise send checkpoint plus a contiguous tail. Register the subscriber and take a synchronization watermark under the same ordering boundary so no update is lost between snapshot and subscription.
6. Bound each receiver queue. If it exceeds 2 MB or five seconds of pending work, mark resync-required. Never drop an arbitrary delta and continue as if its successor were applicable. Coalescing must produce a new valid synchronization transaction relative to an acknowledged state.
7. History API returns version/event metadata, then requested checkpoint/tail. Keep the whole short demo lesson on disk. Browsing old versions must not stop live synchronization. Show Viewed version, Live version, and Return to live.
8. Charge checkpoint, catch-up, metadata, and history requests to network accounting. Prefetched history is still traffic. Show total lesson size and growth.

**Gate:** duplicate/out-of-order/missing/corrupt patch tests, restart between writes, slow receiver, fresh join, stale epoch, and ten-second disconnect all recover. On recovery, hash the decoded canonical pixel buffer and validity mask on both sides; equality proves delivery, not correctness versus the physical board. Keep these two correctness measures separate.

## 8. Phase 5 — complete teacher/student experience and audio

Teacher page: camera selection, calibration, Start/Pause/End, raw/rectified/mask/reconstructed views, detected runtime label, inference failure state, update rate, last version, receiver link, and structured evidence export. Technical metrics belong here or in an expandable diagnostics panel.

Student page: readable board, zoom/fit, Live/Disconnected/Syncing indicator, unobtrusive stale-region legend, history slider with erase markers, Return to live, and Join audio button. On connection loss preserve the last board and state its age. Never show a blank replacement while resynchronizing.

Implement local WebSocket signaling for an audio-only RTCPeerConnection. Teacher microphone permission is requested on localhost (secure-context exception); student reception needs a user gesture for playback. No TURN/cloud dependency in the MVP; disclose LAN-only connectivity and test actual ICE establishment. On reconnect renegotiate audio independently; do not replay old audio after an outage. Handle ended microphone track and permission denial visibly.

Request Opus and a modest bitrate where browser support allows, inspect negotiated SDP/stats, and report actual transmitted bytes. A requested 24 kbps is not an observed rate. Do not describe a board-only run as meeting the existing board-plus-audio proposal.

**Gate:** physical camera + real person + microphone reaches a second browser; erasure, history, and reconnect work while audio plays. Record the actual browser version and any connectivity limitation. Internet disconnected after installation does not break local inference or the LAN session.

## 9. Phase 6 — reproducible quality and network benchmark

Do not postpone the harness until screenshots. Implement it once the protocol works, then feed real recordings into it.

### Dataset and ground truth

Record one ten-minute fixed-camera lesson and microphone audio. Include small plus/minus signs, equals, subscripts, superscripts, a diagram, occlusion, hidden writing, partial/full erasure, and rapid writing. Include a short 60–90 second subset for development. Save original files and hashes. Obtain permission for recognizable people.

Create a timed event CSV: event ID, original timestamp, time first fully visible, region, expected expression, operation, and reference clear frame. Label at least 30 expressions/symbol groups. Define detection latency from **first verifiable visibility** and separately report time hidden behind a presenter. Do not penalize a system for not seeing through a person or hide that delay from the reader.

### Three measured modes

1. CHALKLINE reconstructed board + same audio source.
2. Tuned low-frame-rate camera video + same audio source.
3. Periodic rectified full-board snapshots + same audio source.

Use real-time replay of identical source content/timestamps, real receivers, and actual encoding/decoding. Build a browser replay source from a local video element/canvas capture for video/audio baselines. Automate browser permissions and playback with Playwright. Verify timing and source hashes; do not replace a live-delivery baseline with only an offline output-file size.

On a separate tuning subset choose video resolution/frame-rate/bitrate and snapshot interval/quality per cap. A starting video search is 360p/480p/720p at 1/2/5 FPS; snapshot search is 1/2/5/10-second intervals. Retain the best quality feasible under the shared cap and publish configs. Do not deliberately weaken baselines. Freeze tuning before held-out evaluation.

### Two explicitly different benchmark layers

**A. Application-layer comparison on Snapdragon:** implement a deterministic shared application-byte scheduler for board and snapshot messages, including checkpoint/history/control. Log queued/transmitted/received bytes and delay, with ten-second disconnect at source time 240 s. This validates scheduling and recovery. It does not shape WebRTC UDP, TCP/IP overhead, or the whole laptop network. Label its graphs Application-layer simulation. Never use it alone to claim a 64 kbps total-link result or a fair fully constrained video/audio comparison.

**B. Final wire-level comparison:** route teacher-to-student traffic from the Snapdragon PC through a controlled Linux router/bridge or equivalent verified packet shaper. Prefer a spare Linux machine as a network appliance; if unavailable, prepare a Linux VM/two-namespace benchmark harness and explicitly route all relevant endpoints through it. A VM or WSL merely existing on the laptop is not proof that Windows browser traffic crosses its shaper. Verify routing with capture and observed capped transfer before measuring. If no suitable route is available, preserve A and report B as blocked; do not fabricate a substitute claim. The network appliance does not run CHALKLINE inference.

Commit a router setup/reset script with configurable interface names, a cleanup trap, `tc` rate shaping and `netem` impairment, and packet-capture commands. Verify installed `tc` semantics before composing rate/delay/loss hierarchy. Limit changes to the dedicated test interfaces. Shape the shared egress containing **all board/video/audio/control** traffic, never each stream independently at the full cap. Capture at a declared interface once per direction to avoid double counting. State whether bytes include L2 or IP headers; include retransmissions and reverse traffic separately.

Matrix: 3 methods x 64/128/256 kbps x 3 fixed seeds = 27 ten-minute runs. Use 100 ms one-way added delay and 1% random packet loss as the initial shared impaired profile; insert a ten-second complete outage at 240 s. Document rate units (decimal kilobits), direction caps, burst allowance, queue size, and exact loss placement. Keep a no-impairment reference. Include initial join and recovery bytes; do not truncate the recording to omit expensive checkpoints. Stop at a fixed deadline plus a disclosed fixed recovery window, and report unfinished queues.

### Metrics to generate from raw evidence

- Total and time-series receiver traffic; audio/board/control breakdown where observable; 1-second/10-second bursts; queued bytes and dropped work.
- Visible-change-to-correct-client latency p50/p95/max, and stale-region duration.
- Correct final version/hash, reconnect-to-correct-state delay, initial join delay.
- Symbol transcription on shuffled blind method labels; answer key separate. Record rater count; if only the entrant rated, disclose that limitation rather than calling it independent.
- Same audio prompts and blind listener transcription/intelligibility; include dropout duration.
- False erasures, missed strokes, presenter leakage, and unresolved changes against ground truth.
- Codec/resolution, model hash, hardware, software versions, complete config, seed, source hash, commit, and run ID.

Each run emits manifest JSON, events JSONL, metrics CSV, client captures at predetermined times, and failures. `report_results.py` consumes those files; no numbers typed into the table by hand. Include unsuccessful runs. If 64 kbps fails but 128 kbps works, say that and change the pitch target/claim accordingly.

**Gate:** identical-input comparisons are rerunnable, accounting boundary is explicit, and all headline claims link to raw files. Bandwidth gains belong to the representation/protocol design; they do not establish an NPU advantage.

## 10. Phase 7 — Snapdragon validation: exact execution order

Run the installation and single-inference checks during Phase 1. Run the complete end-to-end checks and performance experiment once the pipeline is ready, before UI polish.

1. Record manufacturer, exact HP model, Snapdragon SoC, Windows build, memory, power mode, AC/battery state, firmware, NPU driver, and interpreter architectures. Verify the actual device identity rather than copying a configured target name into evidence.
2. Copy/clone the same commit and verified model artifacts. Run `setup-snapdragon.ps1`: create x64 host environment and separate native ARM64 inference environment using explicit interpreter paths. Its dependency preflight must verify compatible wheels and fail with actionable instructions, not silently use x64 Python for NPU work.
3. `doctor.ps1` verifies OS/process architecture, exact package versions, model checksums, worker launch, camera, browser, and backend library resolution. Keep export/quantization tools out of the minimal ARM64 environment.
4. Run a single known tensor through strict QNN before launching the product. For the selected runtime, configure HTP, disable CPU EP fallback, and enable provider profiling. The [ORT QNN instructions](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html) document `session.disable_cpu_ep_fallback` and `QnnHtp.dll`; use the selected release's exact registration API. If graph-I/O quantization is assigned to CPU by default, explicitly resolve it or disclose the partition; strict full-graph evidence must not quietly permit it.
5. Verify masks on the saved real frames. A successful provider registration, available-provider list, or NPU Task Manager spike alone does not prove this model executed on NPU. Preserve session settings, logs, successful output, model hash, graph assignment/profile evidence, and timestamps tied to this worker.
6. Run strict QNN camera-to-browser, including occlusion, erasure, audio, and reconnect. Record failures and latency through IPC/preprocessing/postprocessing as well as inference.
7. Disconnect internet and repeat the local flow. Confirm no remote inference endpoint is used.

### Controlled CPU/NPU experiment on the SAME Snapdragon laptop

- Compare native ARM64 CPU inference against native ARM64 QNN inference through the same worker/IPC contract on the same Snapdragon PC. An emulated x64 CPU worker is not the primary CPU baseline.
- Prefer the identical QDQ model on both providers when supported; also report the float CPU model if it is the faster reasonable CPU option. If artifacts/precision differ, label that and compare quality on the same evaluation set. Do not present quantization gains as pure hardware gains.
- Warm up 50 inferences, then measure at least 300 identical inputs per run, three alternating CPU/NPU runs. Capture cold session startup separately. Lock input shape, frame schedule, power mode, and pipeline settings; disclose CPU thread settings and thermal conditions.
- Report inference p50/p95, sustained throughput, host+worker CPU use, full pipeline p95, dropped frames, and mask/board quality. Run a sustained 10-minute lesson in each mode as the practical test.
- Predeclare a useful result: for example >=1.5x inference throughput or >=25% lower combined CPU use at matched 8 FPS, with no material board-quality regression. These are project acceptance targets, not competition requirements or promised findings. Define regression tolerance before runs (initially <=2 percentage points mask IoU/transcription decrease and no extra false erasures on the labeled set).
- If energy cannot be measured repeatably, omit energy/battery claims. Task Manager utilization is supporting context, not power measurement.

**Gate:** strict target execution is proven, both modes work end-to-end, and measured advantages/limitations are disclosed. If advantage is negligible, examine preprocessing/IPC overhead and model shape once; publish the honest result. Never manufacture a speedup to satisfy the narrative.

## 11. Phase 8 — evidence, demo, and release documentation

Create an evidence index that identifies the device, run, source footage, commit and hashes for every result. Keep `snapdragon-cpu` and `snapdragon-qnn` directories unmistakably separate. Include actual screenshots of calibration, segmentation overlay, student preserved board during occlusion, post-erasure update, history, reconnect, and target profiling evidence.

Make a 2–3 minute real demo recording after the interface is stable:

| Time | Visible action and narration goal |
|---|---|
| 0:00–0:20 | Show physical setup and exact target laptop; explain handwriting continuity |
| 0:20–0:40 | Calibrate, start camera, open student link |
| 0:40–1:10 | Write, stand in front, reveal; show last verified writing and stale status |
| 1:10–1:35 | Erase a symbol; show confirmed update and historical state |
| 1:35–1:55 | Disconnect receiver for ten seconds; reconnect to correct live version |
| 1:55–2:20 | Show measured network comparison with accounting label and real run ID |
| 2:20–2:45 | Show actual CPU/NPU result and inference disclosure; state key limitation |

Capture microphone and screen; physically showing the setup may require a phone clip from the user. Do not substitute concept imagery for runtime footage. Verify the recording plays, text is readable, and spoken numerical claims match evidence. If only replay is shown, label replay. Keep a fallback real recorded lesson and deterministic fixture, clearly distinguished from live mode.

Write tested setup guides with exact PowerShell commands, interpreter paths/architecture checks, environment creation, model retrieval/checksum, driver/runtime requirements, camera permission, Start/Stop, student joining, audio permission, and troubleshooting. `start-snapdragon.ps1` defaults to strict QNN and must not conceal fallback. Example intended interface:

```powershell
# On the Snapdragon-powered HP PC:
.\scripts\setup-snapdragon.ps1 -ArmPython '<absolute ARM64 python.exe>' -HostPython '<absolute x64 python.exe>'
.\scripts\doctor.ps1 -RequireNpu
.\scripts\start-snapdragon.ps1 -Source camera:0 -Lan
.\scripts\verify.ps1 -Mode snapdragon
```

Implement these interfaces and replace placeholders in the final setup guide with discovery instructions and a tested example. Never claim these commands have run merely because this plan lists them.

`INFERENCE_DISCLOSURE.md` must tabulate: component, actual process architecture, CPU/GPU/NPU location, model/precision, fallback behavior, evidence path, and verified date. Segmentation is the intended NPU task; capture, transforms, temporal logic, encoding, storage, and transport remain CPU/browser work. All-application-on-NPU is not a valid claim.

Finally update README, proposal status, evaluation plan, and submission description to reflect measured work. Preserve concept labels where those images remain. Run the fresh-checkout setup path, focused tests, full demo, and evidence consistency check. Prepare changes for review; pushing/publication follows the user's authorization. Leave Unstop Submit untouched.

## 12. Failure decisions: what Sol should do instead of getting stuck

| Blocker | Required response |
|---|---|
| Required hardware/runtime inaccessible | Record the exact pending gate; complete independent code, fixtures, and documentation without claiming hardware execution |
| No physical board/camera access | Ask once for a mounted camera/short clip, continue with labeled fixtures; do not claim live proof |
| QNN model fails to load | Save error and versions; check artifact/static shapes/operator support/package pairing; one bounded model alternative |
| ARM64 OpenCV dependency issue | Use the specified x64 host/native worker split; do not rewrite the product |
| Person masks miss hands | Expand mask, motion uncertainty, longer confirmation; evaluate added latency and report residual risk |
| 64 kbps cannot carry full lesson | Keep measured failures; report the lowest proven useful cap and its latency/quality |
| No controlled wire-level route | Publish application comparison with explicit limits; total-link benchmark remains incomplete |
| No measurable NPU improvement | Report honestly; try one targeted optimization; do not claim that bandwidth savings prove Snapdragon advantage |
| External publishing/account gate | Complete local code/evidence/docs first and state the exact blocked action |

## 13. Completion checklist and priority

The time allowances are scheduling aids. This is several focused build sessions plus hardware validation and a multi-hour benchmark matrix, not a guaranteed overnight production app. Spend effort in this order: working masks/runtime -> camera flow -> conservative board state -> correct delivery/history -> audio -> reproducible measurements -> visual polish.

**Working MVP on Snapdragon:** real model; live/file source; calibration; verified board engine; browser history/recovery; working audio; fixture and physical evidence; versioned protocol tests; benchmark harness; tested installation scripts. Mark only passed items complete.

**Validated release on Snapdragon:** exact HP/Snapdragon identity; native strict QNN inference; actual camera-to-browser session; native CPU/NPU comparison; real constrained-network results or explicit limitation; readable screenshots; playable short recording; reproducible setup; accurate disclosure.

**Do not declare the user's full outcome complete** while live camera proof, actual target execution, credible Snapdragon comparison, or requested benchmark/evidence remains missing. The user can choose to submit a more limited entry, but Sol must present the remaining gaps plainly.

## 14. Copy-paste prompt to start Sol

> Implement CHALKLINE using `D:\CHALKLINE\repository\docs\SOL_BUILD_HANDOFF.md` as the build specification. Read it and the existing proposal first. Build exclusively for the Snapdragon-powered HP Windows PC workflow described in the plan, with native ARM64 strict-QNN inference. Keep repository documentation, setup, product copy, and demo Snapdragon-focused. Follow the prescribed phase gates and persist through implementation and verification. Keep BUILD_STATUS.md so you can resume without rereading everything. Preserve handwriting evidence, distinguish unknown/stale regions, and implement real calibration, presenter segmentation, changes/erasures, versioned patches, history, reconnect, audio, benchmark harness, setup instructions, and evidence collection. Use the model/runtime risk spike early. Do not create another proposal or a mock UI in place of the app. Do not use subagents, deploy cloud services, or press Unstop Submit. Do not fabricate numbers or substitute bandwidth gains for NPU proof; record actual execution only after verification. Start Phase 0 and continue; ask only for genuinely missing hardware/input while completing independent work.
