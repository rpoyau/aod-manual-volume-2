# Matter I relational-time to SI-seconds contract

Proposed Manual application contract, R02, 26 October 2026. This specifies the next implementation. It is not implemented in PR head `81326ecb6d42107d00e9f2b626ed720f8b5b58ba` and is not a physical calibration result.

## RT-SI-1. Committed relational origin and measurement scope

**Setup.** [Scope: a declared Matter I measurement protocol P.] Choice SI-1. Retain the native relational record RT for a common committed window W=(u,v), the two distinct recurrent lineages, immutable return identities, committed trace prefixes, repeated contacts, orientation, bias, unwrapped lag, drift and directional RCD. Preserve the existing conventions: contact cuts in [u,v], reclosures in (u,v]. Record the actual reference reclosure increment N_r, not only the cadence ratio. The reference increment must be positive for a ratio.

The relational “now” is the declared committed comparison cut with its bound histories. The native origin/anchor fixes identity and event order. An external epoch is a separate optional report coordinate. Neither k, one Hamming-1 step, a closure phase, a dwell sample, 6n traversals nor an RCD support count acquires seconds through renaming.

**Derivation.** Consequence SI-1. A dimensionless cadence ratio does not determine elapsed seconds. Proof sketch. Multiplying both recurrence increments by the same positive integer preserves their ratio. Recovering a duration additionally requires the reference increment and an operational scale map. The SI output must therefore bind the underlying window and histories, not discard them after computing a ratio.

**Specialization.** For a claimed native AOD map, the source admission obligations remain required. A conditional declared model or conventional benchmark may use its own explicitly declared state/observation premises and execute while native admission remains unresolved. Its output classification must say which case applies.

**Falsification.** Reject a seconds claim with an absent observation map, missing reference identity/window, incompatible prefixes or ambiguous physical event association. Changing a display epoch or serialization must not change the same physical interval. This does not make physical dwell durations irrelevant: actual dwell dynamics may change the measured interval through the declared map.

**Provenance.** Owner M1 plan §§3.9–3.11 and 5.2; current Main `sections/06_wave_state_relational_time.tex`, comparison window definition; current Manual §§5–6. The owner plan is an owner proposal, not a silently substituted released Main version.

## RT-SI-2. Explicit SI realization map

**Setup.** [Scope: one calibrated reference channel on W.] Choice SI-2. The protocol supplies an observation model

\[
 C_r(W)=G_{\mathcal P}(\Gamma^W_{\le v},\Gamma^\times_{\le v},N_r,
 \psi,\Lambda,\rho^D;\theta,\text{observations}), \tag{SI.1}
\]

where C_r is the accumulated physical oscillator cycle count, including fractional endpoint phase when measured, and theta contains calibrated parameters. Its association with native reclosures must be evidenced. A restricted affine example is C_r=alpha N_r+beta_v-beta_u; it is an application assumption whose parameters and residuals need calibration. The native phase unit 1_C is not automatically a physical oscillator cycle or 2pi radians.

Use the exact defining value nu_Cs=9,192,631,770 Hz. For an output connected by a known ideal synthesis ratio a, let f_0=a nu_Cs. Actual synthesis imperfections belong in the realization budget. Let y_bar be the effective mean fractional frequency offset of that output relative to f_0 over this window, in the declared target time coordinate. Let d be the signed correction from the observed gate endpoints to the intended measurement endpoints, expressed in seconds. Assign each physical effect once, either within G, y_bar or d, with explicit shared-input covariance.

**Derivation.** Corollary SI-2. Under Choice SI-2, the interval estimate is

\[
 \widehat T(W)=\frac{\widehat C_r(W)}{f_0(1+\widehat{\bar y}_r(W))}+\widehat d(W).
 \tag{SI.2}
\]

Derivation. The effective frequency is f_0(1+y_bar); dividing the measured cycle accumulation by that frequency gives the observed gate interval. Adding the defined endpoint correction yields the measurand. For varying frequency, derive y_bar from the actual weighted/integrated measurement model; do not substitute an unrelated averaging window. Equation (SI.2) is a declared measurement equation, not an AOD theorem that fixes a clock rate.

**Specialization.** Corrected cycles C_r^0 at the ideal Cs rate give T=C_r^0/nu_Cs. Only a justified G can identify C_r^0 with a function of native returns. A real reference may instead be a traceable oscillator, a Cs realization or an Rb secondary representation. Rb's recommended frequency carries uncertainty; it cannot be treated as an exact defining constant. A synthesized output's nominal frequency need not be 9.192 GHz.

For an Rb channel one may choose a fixed nominal numerical rate for bookkeeping, but uncertainty of the recommended physical rate remains in y_bar and its covariance. Alternatively, use a calibrated f_ref as an uncertain input to T=C_r/f_ref+d. These are alternative parameterizations of one budget; do not count the same frequency uncertainty in both.

**Calibration.** Bind device/channel, oscillator and transition identities, calibration certificate or primary measurement record, nominal ratio, correction estimates, validity interval and drift, raw observations, calibration data/exposure, parameter covariance, uncertainty coverage and traceability chain. A webpage stating the SI definition supplies no device calibration.

Declare the measurand as a local proper-time interval at a specified point or as an interval referred to a stated coordinated time scale. Local proper time does not receive a blanket correction to a global gravitational potential. Comparisons between separated clocks and coordinated scales need applicable motion/potential/transfer corrections and their uncertainties. This external metrological model does not redefine native ontology. UTC epoch reporting, if used, needs a separate time-scale conversion and leap-second convention.

**Falsification.** A faster reference gives a shorter inferred interval for fixed observed cycles. An ideal known frequency divider must preserve both T and its propagated uncertainty when counts, nominal frequency and covariance are transformed consistently. Altering external report calibration must not rewrite already committed native events. An online result cannot consume future calibration data while claiming to have been available at the earlier “now”; later recalibration must be recorded as retrospective.

**Provenance.** Equation (SI.1), Choices SI-1/SI-2, owner plan §3.11, current observation-map profile.

**Literature note.** Definition: [BIPM SI second](https://www.bipm.org/en/si-base-units/second). Realization and proper-time distinction: [CCTF mise en pratique, §§3.1–3.3](https://www.bipm.org/documents/20126/41489667/SI-App2-second.pdf/3c76fec8-04d9-f484-5c3c-a2e280a0f248). Coordinated-scale interpretation: [SI Brochure, version 4.01, §§2.3.1 and 2.3.6](https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf).

## RT-SI-3. Uncertainty of the reported seconds

**Setup.** [Scope: valid first-order propagation about the stated estimates.] Choice SI-3. Let z=(C_r,y_bar,d), with their joint covariance Sigma_z in the corresponding units. The expanded input vector must include the calibration/observation parameters from (SI.1) whenever their contribution has not already been propagated into Sigma_z. Missing uncertainty or covariance is unknown. A zero term requires a stated reason; dimensional exactness of a count does not prove that the physical event detector counted the intended events without error.

Validate variable ordering, dimensions, units, symmetry and positive semidefiniteness before propagation. For a rounded published matrix, declare and justify the numerical tolerance; do not silently clip negative variances or invent correlations to obtain a preferred error bar.

**Derivation.** Corollary SI-3. Differentiating (SI.2) gives

\[
 J=\left(\frac{1}{f_0(1+\bar y)},
 -\frac{C_r}{f_0(1+\bar y)^2},1\right),\qquad
 u_c^2(T)=J\Sigma_zJ^{\mathsf T}. \tag{SI.3}
\]

Shared inputs are preserved through the cross terms. If the measurand is an endpoint difference, use

\[
 u^2(x_v-x_u)=u^2(x_v)+u^2(x_u)-2\operatorname{Cov}(x_v,x_u). \tag{SI.4}
\]

Common offsets can cancel; a persistent frequency-scale uncertainty can accumulate with interval length. For a discretized fractional-frequency history with duration weights w, the frequency contribution to time-error variance is w^T Sigma_y w. Independence and a 1/sqrt(n) reduction cannot be assumed for clock noise, drift or a shared systematic contribution.

**Specialization.** The exact defining constant has no uncertainty; realized clock rates and measurement corrections do. Keep measurement error, estimated correction, residual uncertainty and model discrepancy separate. Evaluate the linear approximation: a clock shift q B^2 at mean field zero can have a nonzero mean correction and uncertainty despite a zero first derivative. Use higher-order propagation or a justified distribution-propagation method when needed. Discrete cycle slips require an explicit ambiguity/outlier model, not an arbitrary small Gaussian error bar.

**Calibration.** For every budget row retain: effect and input identity; applicable device/window; estimate and sign; unit; standard uncertainty; evaluation method (Type A/Type B as appropriate); distribution/coverage information; sensitivity; covariance group; source; included-in-aggregate relationship; and correction status. Examples of effects to assess for applicability are reference realization, magnetic/thermal/collision/motion shifts, oscillator noise and servo effects, endpoint phase/detection/quantization, dead time and extrapolation, propagation/electronics delay and link asymmetry, relativistic transfer, and observation-model parameters/residuals. Do not impose irrelevant corrections or add already included components a second time.

Report T_hat, u_c(T) and seconds. If reporting U=k u_c, state k and the coverage interpretation. Allan deviation or TDEV may characterize stability under an acquisition/noise model; neither is automatically the complete accuracy/uncertainty budget. Specify averaging weights, noise assumptions, sampling and dead time.

**Falsification.** Covariance omission must change the appropriate test result; known common contributions must cancel only where the measurement equation cancels them. Standard-uncertainty multiplication by g transforms covariance by g^2. A materially incomplete budget may be reported as partial or bounded with its scope, but cannot support a claim of complete precision.

**Provenance.** Equations (SI.1)–(SI.4) and their declared measurement premises; exact synthetic arithmetic in `scripts/check_metrology_examples.py`.

**Literature note.** Correction and correlated propagation: [JCGM 100:2008, §§3.2, 5.2 and 6](https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf). Model formulation/nonlinearity: [JCGM GUM-6:2020](https://www.bipm.org/documents/20126/2071204/JCGM_GUM_6_2020.pdf). Stability versus accuracy: [NIST, Measuring Time and Comparing Clocks, pp. 5–6](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=915305).

## RT-SI-4. BIPM reference-data treatment

Preserve the source-described ratio basis and the numerically supported Hz-squared interpretation of the supplied output covariance as separate fields. Under the declared Hz-squared interpretation, normalized ratios to the exact Cs value use Sigma_ratio=Sigma_Hz/nu_Cs^2. General ratios use their full Jacobian. This is a transformation of published frequency estimates, not a new physical clock realization.

Retain the 2.35 standard-uncertainty recommendation multiplier and its squared covariance effect, distinct from a coverage factor. Apply it at the intended reporting level once. The additional fractional random-effect term 5.324065020e-17 belongs to reproducing the documented adjustment; do not append it again to output uncertainties that already include that procedure. Preserve all 153 source rows, seven effective exclusions and 1,168 correlations.

For new observations, add the actual device/transfer/observation budget only to the extent it is not already included or correlated. Do not add a fresh independent Cs uncertainty to a published aggregate simply because Cs appears in its traceability chain. Preserve the H paper's 0.002 Hz aggregate scope and unknown quantitative covariance. H and Rb target exposure remains recorded; neither the unit definition nor a fitted calibrant is an independent prediction target.

The calibration and comparison stages may proceed with clearly declared models. Complete native admission, a new realization of the SI second and independent prediction each require their own evidence.

## RT-SI-5. Required AOD prediction after calibration

The owner amendment in `PREDICTION_OBJECTIVE.md` supplies the completion criterion. Use the preferred Cs-133 anchor/H-1 comparison route or justify an alternative traceable hydrogen reference. The AOD dynamics and atomic observation map must calculate the nontrivial ratio or response; the SI anchor then sets its units. Preserve the full uncertainty and exposure contract when producing the numerical prediction and residual. A conventional benchmark or a report of the calibrant itself does not complete this AOD prediction task. Agreement is not guaranteed or required for an honest, completed falsification test.
