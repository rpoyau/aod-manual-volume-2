# Owner amendment: AOD predictions after anchoring relational time to SI seconds

26 October 2026. This amendment governs the intended scientific outcome of the next Matter I update. It supplements the R02 metrology contract and supersedes any reading of the earlier task that would treat a conventional benchmark or a calibrated clock report as the completed objective.

The required end-to-end result is an AOD-derived forward calculation: atomic configurations and their recurrent, coupled histories produce a relational observable; a declared observation/calibration map anchors it to SI seconds; the frozen model then produces a numerical observable for comparison with measurement. The conventional benchmark remains a verification aid. The AOD calculation is a separate required deliverable.

## Preferred first experiment: Cs-133 anchor, hydrogen comparison

**Setup.** [Scope: a declared atomic application of AOD.] Choice PRED-1. Construct identified Cs-133 and H-1 configurations under one declared dynamics/observation model. Bind recurrent histories, common windows, contacts, handedness, phase bias, unwrapped lag, drift and directional duration. Define the physical transition observable and its connection to these histories. Preserve the native-versus-metrological type distinction in the owner M1 plan §§3.10–3.11.

Use Cs-133 to set the SI frequency/time scale through the realization and uncertainty contract. Reserve the hydrogen transition quantity for evaluation rather than fitting its splitting, period or an equivalent per-isotope scale parameter. Non-target measured inputs may be used when their provenance, role and resulting conditional nature are explicit.

**Derivation.** Let R_hat_AOD be the dimensionless H/Cs frequency ratio calculated from the AOD dynamics and the declared atomic observation map. It is not automatically the bare ratio of native reclosure counts. Once that map has been established, the ideal-reference reporting equations are

\[
 \widehat\nu_{\mathrm H}=\widehat R_{\mathrm{AOD}}\,\Delta\nu_{\mathrm{Cs}},
 \qquad\Delta\nu_{\mathrm{Cs}}=9\,192\,631\,770\ \mathrm{Hz},
 \qquad\widehat T_{\mathrm H}=\widehat\nu_{\mathrm H}^{-1}.
\]

These equations convert a model result to hertz and seconds. They do not determine R_hat_AOD. That is the scientific calculation the update must attempt and expose. A synthetic choice of R or a transcribed measured ratio does not satisfy this deliverable.

**Calibration.** Record which parameters are determined by the reference and which additional data constrain the model. Fixing one overall SI scale does not justify arbitrary independent Cs and H scale factors. All scale, observation and correction uncertainties remain in the joint budget. For a parameterization with an uncertain realized reference frequency f_ref,

\[
 u^2(\widehat\nu_{\mathrm H})\simeq
 f_{\rm ref}^{2}u^2(\widehat R)
 +\widehat R^{2}u^2(f_{\rm ref})
 +2\widehat R f_{\rm ref}\operatorname{Cov}(\widehat R,f_{\rm ref}).
\]

If the defining Cs value is used as exact, physical realization uncertainty must instead appear in the observation/calibration parameters; do not count it twice. Within the valid linear regime, u(T_hat)=u(nu_hat)/nu_hat^2. Use the fuller propagation required by `SI_ANCHOR_CONTRACT.md` when this approximation is inadequate.

**Specialization.** Hydrogen may be the working reference if its realization is independently characterized and traceable to SI. Its measured frequency carries uncertainty. Reversing the same H/Cs ratio is the same comparison expressed differently, not a second independent validation. If both Cs and H transition values are fitted, those values are calibration results; reserve another condition, response or transition for the subsequent prediction.

**Falsification.** Freeze the model, observation map, calibration parameters and declared target before running the scoring stage. Emit the predicted ratio, frequency, period and supported uncertainty before the scorer reads the evaluation values. Preserve the existing record that H and Rb values have already been seen: software separation does not create blinding retroactively. The known H comparison is a retrospective test of predictive calculation. Select an additional eligible out-of-sample or prospective test with its own exposure record for an independent prediction claim.

Compare predicted and measured values using their joint covariance, including shared-reference contributions. Report disagreement as a result. Do not retune the tested target silently or require agreement as a condition for reporting a completed scientific test.

**Provenance.** Owner clarification of 26 October 2026; owner M1 plan §§3.9–3.12; `SI_ANCHOR_CONTRACT.md`; the existing H/Cs source inventory and exposure ledger.

**Literature note.** SI anchor: [BIPM definition of the second](https://www.bipm.org/en/si-base-units/second). Realization: [CCTF mise en pratique](https://www.bipm.org/documents/20126/41489667/SI-App2-second.pdf/3c76fec8-04d9-f484-5c3c-a2e280a0f248). The current inventory retains the historical hydrogen measurement and its 0.002 Hz reported uncertainty; it does not supply a new clock calibration.

## Completion criteria

1. An executable AOD candidate calculates the designated relational/atomic observable from its declared dynamics and inputs, with the origin of every physical/model parameter exposed.
2. The reference anchors the scale and carries its applicable metrology budget. The comparison target is not used to choose its own prediction through a hidden equivalent parameter.
3. A prediction artifact contains the ratio, frequency in Hz, period or mapped interval in seconds, relevant lag/drift/duration outputs where their physical maps exist, uncertainty scope, model/calibration hashes and target/exposure roles.
4. A separate comparison artifact reports measured values, residuals, shared-reference covariance and the appropriate retrospective/out-of-sample classification.
5. A controlled intervention demonstrates how the implemented relational dynamics affects the predicted observable, while reference calibration alone cannot manufacture the target relation. Use a meaningful parameter/coupling change and preserve prior committed histories.

If the admitted/declared premises do not yet determine a numerical AOD prediction, demonstrate the specific underdetermination and identify the minimum additional modeling premise or needed data. Deliver valid intermediate simulations, but mark the end-to-end prediction objective incomplete. Do not substitute another inventory, a conventional-physics calculation, a schema-only pending result or an invented number for the requested AOD calculation.

This amendment sets the objective; it reports no completed AOD atomic prediction, successful empirical agreement or new native admission.
