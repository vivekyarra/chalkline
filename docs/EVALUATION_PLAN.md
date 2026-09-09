# Evaluation protocol

## Question

At equal constrained bandwidth, does a versioned board-and-audio stream preserve handwritten lesson content more reliably than tuned low-frame-rate video or periodic snapshots plus audio?

## Fixed input

Record a ten-minute, fixed-camera blackboard lesson containing small operators, superscripts, a diagram, presenter occlusion, partial erasing, full erasing, and rapid writing. Keep the original video and a manually recorded sequence of correct board states as ground truth.

## Compared methods

1. CHALKLINE board patches plus audio.
2. Tuned low-frame-rate video plus audio.
3. Periodic full-board snapshots plus audio.

Run each at 64, 128, and 256 kbps total application traffic. Inject the same delay, loss, and ten-second disconnection profile. Record configuration and actual bytes for every run.

## Measurements

- Blind transcription accuracy for predefined board symbols and expressions.
- Listener-rated audio intelligibility using the same source audio.
- Median and worst-case time from visible board change to correct client state.
- Correctness and time to recover after reconnection.
- Total application and transport bytes.
- CPU load, NPU utilization or profiler evidence, and energy only where measurement is repeatable.
- Failure log for stale regions, missed writing, false erasures, and checkpoint inconsistencies.

## Claim gate

The 64 kbps statement remains a target until an end-to-end run stays inside the cap and the disclosed quality measurements support it. Any CPU fallback, dropped update, or unrecoverable state is reported with the result.

