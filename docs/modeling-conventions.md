# Modeling conventions and analytical reference

[简体中文](建模约定与解析基准.md)

The physical inputs are defined in `configs/reference_parameters.json`. Calculations use SI units, exp(jωt), RMS phasors, copper conductivity 5.8×10⁷ S/m, μr=1 and 20 °C. The primary transport case is 200 kHz and 20 A RMS; the corresponding peak current is 20√2 A. Each numerical case specifies its return and exterior boundary. Current density and loss hotspots are electrical quantities; temperature requires a thermal model.

## Copper area and length

At a 4 A/mm² current-density limit, 20 A requires at least 5 mm² nominal copper area. The original Q1 diameter of 2 mm gives π mm² and 6.366197724 A/mm²; this case is retained for calibration. A 640 × 0.100 mm bundle has 5.026548246 mm² nominal circular area, giving 3.978873577 A/mm² and an equal-area solid diameter of 2.529822128 mm. Exactly 5 mm² instead gives 2.523132522 mm. The actual polygonal or voxel area is retained in comparisons.

Every per-metre quantity refers to axial length. For strand areas Ai and actual arc lengths ℓi, DC resistance is `(Σ σAi/ℓi)^−1` and copper volume is `Σ Aiℓi`. Equal nominal cross-section can therefore coexist with different copper volumes per axial metre.

## Isolated round-wire reference

For radius a=1 mm, define δ=1/√(πfμσ) and κ=(1+j)/δ. With modified Bessel functions I₀ and I₁:

```text
Jz(r) = It κ I₀(κr) / (2πa I₁(κa))
zint = κ I₀(κa) / (2πaσ I₁(κa))
rdc = 1/(σπa²), rac = Re(zint), p = |It|²rac
```

At 200 kHz, δ=0.147771654900 mm, rdc=5.488101485927 mΩ/m, rac=20.016203627649 mΩ/m, rac/rdc=3.647199979624 and p=8.006481451060 W/m. These are analytical internal-field values, recorded in `configs/reference_values.json`. Independent current and Joule integrals check normalization and RMS power. External inductance depends on the return and belongs to the specified port model.

## Common terminals and transposition

Insulated strands connected in parallel satisfy `Zi+e=V1` and `1ᵀi=It`. Solve this augmented system for the complex strand currents and common voltage. With Q=IN−11ᵀ/N and a unique port solution, equal complex currents require and imply `Q[(It/N)Z1+e]=0`. With zero independent excitation and nonzero It, this reduces to equal row sums of Z.

The segmented approximation `Ztot=Σ Δzs PsᵀZsPs` retains physical strand identities and permutation directions. Reordering the same additive weighted blocks leaves their sum unchanged. Actual trajectories additionally require periodicity, clearance, curvature, arc length and appropriate field degrees of freedom.

## Comparing loss

Report absolute Rac, Rac/Rdc, loss, copper volume, arc-length growth and complex-current deviation together. In pure transport, compare input active power with all dissipation inside the chosen boundary. With an independent imposed field, include its supplied power and report excitation-dependent absorption. RT0 imposed-field loss and intrinsic transport resistance have different definitions.

Traditional multilevel Litz is the structural comparison baseline. Candidate improvements must exceed relevant numerical uncertainty. Acceptance targets and retained failures are defined in [the acceptance guide](../tests/ACCEPTANCE.md).
