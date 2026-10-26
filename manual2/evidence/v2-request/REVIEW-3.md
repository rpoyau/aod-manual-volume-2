# R02 amendment intake and review

The governing endpoint is now an executable AOD forward calculation, preferably Cs-133 reference → H-1 comparison. A conventional benchmark is supporting verification. The AOD dynamics and atomic observation map must determine the nontrivial H/Cs ratio; the reference sets the SI scale. Separate prediction and comparison artifacts are required. This review accepts that revised scope; it does not report implementation or an atomic prediction.

Reviewed PR: https://github.com/rpoyau/aod-manual-volume-2/pull/1

Head: `81326ecb6d42107d00e9f2b626ed720f8b5b58ba`  
Tree: `1c4fa29a786f4ee84aa866787c7c8b928deb9e9b`

The remote head remains unchanged. Hosted run 40284951264 remains successful. No repository or GitHub mutation was performed in this review.

The five tracked skills remain the applicable authority, using their previously reviewed contents and the owner-resolved scope in `manual2/evidence/fusion-request.json`. AF premises belong in GM Setup; the Manual owns the application and calibration maps, without rewriting Main ontology.

## Verification

The supplied archive is 63,942 bytes, SHA-256 `6bd43011a84a0b2c976ec8f43d50d48911e3365ddad5632212f5bf21a9d7a585`. CRC, all 26 manifest entries and complete coverage passed. The 14 synthetic arithmetic checks passed normally and under optimized Python. They are not executions of the 18 planned SI integration checks or the AOD atomic prediction. Results are in `verification.json`.

## Required acceptance mapping

Retain the original 39 IDs and the 18 planned SI IDs. Explicitly map the five completion criteria in `PREDICTION_OBJECTIVE.md` to executable assertions:

| Objective criterion | Required evidence |
| --- | --- |
| 1. AOD forward calculation | Cs/H configurations under one model law, a calculated ratio, and the origin and role of every model/physical parameter. A measured-ratio transcription or a stipulated ratio fails this criterion. |
| 2. Scale calibration and target separation | Cs calibrates the common scale. No H frequency, reciprocal period, fitted splitting or hidden equivalent isotope-specific gain determines its own tested prediction. All applicable uncertainty enters once. |
| 3. Prediction artifact | Freeze and hash model, observation map, inputs and calibration. Write ratio, frequency, transition period, uncertainty scope and exposure roles before scoring. A changed evaluation value leaves prediction bytes unchanged. |
| 4. Comparison artifact | Separate target ingestion and residual calculation, including prediction/measurement covariance and shared-reference effects. Target mutation changes the residual; it cannot rewrite the prediction. Disagreement is retained. |
| 5. Causal intervention | A controlled change to relational dynamics changes the mapped observable at a strictly later stage while preserving committed prefixes. Changing an external epoch or serialization cannot manufacture that effect. |

These are planned assertions, not new completed acceptance results. They close a bookkeeping gap: the 18 SI rows address metrology but do not explicitly enumerate all of the amended prediction requirements.

## Clarifications for implementation

The predicted transition period `T_H = 1/nu_H` and the measured interval `T(W)` are different quantities. Frequency and its reciprocal are two reports of one prediction, not two independent empirical tests. The interval additionally needs a bound reference count, observation map and measurement window.

The exact Cs defining value supplies units. A conditional ideal-reference prediction carries its applicable model/input uncertainty. A realized clock or device interval additionally requires its actual calibration and observation budget. Preserve realization uncertainty where it enters; do not invent a device record or duplicate a contribution already included in published aggregate uncertainty. Literature note: [BIPM second](https://www.bipm.org/en/si-base-units/second); [CCTF realization guidance](https://www.bipm.org/documents/20126/41489667/SI-App2-second.pdf/3c76fec8-04d9-f484-5c3c-a2e280a0f248).

The known hydrogen target remains retrospective even with strict software separation. Reserving another eligible observable or condition is necessary for a separate independence claim when both Cs and H have been fitted. Model/parameter selection history must remain visible.

SI-13's rounding criterion must account for rounding in both covariance inputs and reported uncertainties. A half-last-digit test against the output alone is insufficient; retain the documented Hz² interpretation and a justified propagation/rounding check.

If the declared premises cannot determine the ratio, identify the specific free mapping or dynamical parameter, show how admissible alternatives change the result, and state the smallest additional premise or observation needed. Continue independent v2 and metrology work, but keep the prediction objective incomplete. A conventional calculation or a precise-looking number does not substitute for that derivation.
