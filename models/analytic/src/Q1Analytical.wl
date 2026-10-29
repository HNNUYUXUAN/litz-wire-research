(* Isolated long round wire; SI, exp(+j omega t), RMS. *)
BeginPackage["LitzAnalytical`"];
RoundWireSolution::usage = "RoundWireSolution[inputs] computes internal impedance and independent area integrals in SI.";
RunQ1Calibration::usage = "RunQ1Calibration[root, runID] archives a local analytical calibration.";
Begin["`Private`"];

RoundWireSolution[p_Association] := Module[
  {wp = 50, f, sigma, mu, a, current, omega, delta, kappa, z, rdc,
   density, currentIntegral, powerIntegral, lowFrequency, lowKappa, lowZ},
  (* Recover decimal configuration values as rational inputs before high precision evaluation. *)
  f = Rationalize[p["frequency_Hz"], 10^-12];
  sigma = Rationalize[p["conductivity_S_per_m"], 10^-12];
  mu = 4 Pi 10^-7 Rationalize[p["relative_permeability"], 10^-12];
  a = Rationalize[p["q1"]["solid_diameter_m"], 10^-12]/2;
  current = Rationalize[p["current_RMS_A"], 10^-12];
  omega = 2 Pi f;
  delta = N[Sqrt[2/(omega mu sigma)], wp];
  kappa = (1 + I)/delta;
  z = kappa BesselI[0, kappa a]/(2 Pi a sigma BesselI[1, kappa a]);
  rdc = N[1/(sigma Pi a^2), wp];
  density[r_?NumericQ] := current kappa BesselI[0, kappa r]/(2 Pi a BesselI[1, kappa a]);
  currentIntegral = 2 Pi NIntegrate[density[r] r, {r, 0, a},
    WorkingPrecision -> wp, AccuracyGoal -> 30, PrecisionGoal -> 30];
  powerIntegral = (2 Pi/sigma) NIntegrate[Abs[density[r]]^2 r, {r, 0, a},
    WorkingPrecision -> wp, AccuracyGoal -> 30, PrecisionGoal -> 30];
  lowFrequency = 1/1000; (* positive frequency, never substitute zero into Bessel quotient *)
  lowKappa = N[Sqrt[I 2 Pi lowFrequency mu sigma], wp];
  lowZ = lowKappa BesselI[0, lowKappa a]/(2 Pi a sigma BesselI[1, lowKappa a]);
  <|"delta_m" -> delta, "rho_ohm_m" -> N[1/sigma, wp],
    "area_m2" -> N[Pi a^2, wp], "Jdc_A_per_m2" -> N[current/(Pi a^2), wp],
    "Rdc_ohm_per_m" -> rdc, "Rac_ohm_per_m" -> Re[z],
    "Xinternal_ohm_per_m" -> Im[z], "Linternal_H_per_m" -> Im[z]/omega,
    "Rac_Rdc" -> Re[z]/rdc, "loss_W_per_m" -> current^2 Re[z],
    "current_integral_real_A" -> Re[currentIntegral], "current_integral_imag_A" -> Im[currentIntegral],
    "current_integral_relative_error" -> Abs[currentIntegral - current]/Abs[current],
    "joule_integral_W_per_m" -> powerIntegral,
    "power_integral_relative_error" -> Abs[powerIntegral - current^2 Re[z]]/(current^2 Re[z]),
    "low_frequency_Hz" -> N[lowFrequency, wp], "low_frequency_Rac_Rdc" -> Re[lowZ]/rdc,
    "profile" -> Table[With[{r = a t/100, j = density[a t/100]},
      {N[r, 18], N[Re[j], 18], N[Im[j], 18], N[Abs[j], 18]}], {t, 0, 100}]|>
];

RunQ1Calibration[root_String, runID_String] := Module[
  {start = AbsoluteTime[], startUTC = DateString[TimeZoneConvert[Now, 0], "ISODateTime"], output, p, result, ref, display, errors, env},
  output = FileNameJoin[{root, "outputs", runID}];
  If[DirectoryQ[output], Return[Failure["RunDirectoryAlreadyExists", <|"run_id" -> runID|>]]];
  CreateDirectory[output, CreateIntermediateDirectories -> True];
  p = Import[FileNameJoin[{root, "configs", "reference_parameters.json"}], "RawJSON"];
  ref = Import[FileNameJoin[{root, "configs", "reference_values.json"}], "RawJSON"]["values"];
  result = RoundWireSolution[p];
  display = <|"delta_mm" -> 1000 result["delta_m"],
    "rho_ohm_m" -> result["rho_ohm_m"],
    "Q1_Rdc_mohm_per_m" -> 1000 result["Rdc_ohm_per_m"],
    "Q1_Rac_mohm_per_m" -> 1000 result["Rac_ohm_per_m"],
    "Q1_Xint_mohm_per_m" -> 1000 result["Xinternal_ohm_per_m"],
    "Q1_Rac_Rdc" -> result["Rac_Rdc"], "Q1_P_W_per_m" -> result["loss_W_per_m"],
    "Q1_area_mm2" -> 10^6 result["area_m2"], "Q1_Jdc_A_per_mm2" -> result["Jdc_A_per_m2"]/10^6|>;
  (* Compare against the exact binary values actually stored by RawJSON; do not cancel at machine precision. *)
  errors = Association@KeyValueMap[(#1 -> Abs[#2 - Rationalize[ref[#1], 0]]/Abs[Rationalize[ref[#1], 0]]) &, display];
  env = <|"WolframVersion" -> $Version, "SystemID" -> $SystemID,
    "kernel_process_ID" -> $ProcessID, "working_precision_digits" -> 50,
    "phasor" -> "exp(+j omega t), RMS", "source_model" -> "isolated_long_round_conductor_internal_impedance_Bessel_solution",
    "execution_status" -> "executed_checks_pending", "run_id" -> runID,
    "elapsed_seconds" -> AbsoluteTime[] - start, "start_UTC" -> startUTC|>;
  Export[FileNameJoin[{output, "parameters.json"}], p, "RawJSON"];
  Export[FileNameJoin[{output, "results.json"}], <|"metadata" -> env,
    "SI_values" -> N[KeyDrop[result, "profile"], MachinePrecision],
    "display_values" -> N[display, MachinePrecision],
    "reference_relative_errors" -> N[errors, MachinePrecision],
    "precision_diagnostics" -> Association@Map[(# -> ToString[InputForm[result[#]]]) &,
      {"current_integral_relative_error", "power_integral_relative_error", "current_integral_real_A", "joule_integral_W_per_m"}],
    "precision_note" -> "Zero numerical residuals mean unresolved at working precision, not exact zero. Wolfram decimal expressions retain precision metadata. Reference errors compare the binary JSON values without machine-precision cancellation."|>, "RawJSON"];
  Export[FileNameJoin[{output, "radial_current_density.csv"}],
    Prepend[result["profile"], {"r_m", "Re_J_A_per_m2", "Im_J_A_per_m2", "Abs_J_A_per_m2"}], "CSV"];
  Export[FileNameJoin[{output, "model_assumptions.md"}],
    "# Q1 analytical calibration\n\nSI; exp(+j omega t); RMS. Isolated infinitely long round conductor, copper sigma=58 MS/m, mu_r=1, 20 C. Internal impedance only; remote return external inductance excluded. No independent applied field. Radius=1 mm, f=200 kHz, total current=20 A RMS. Q1 Jdc exceeds 4 A/mm^2; retained as specified calibration, not a compliant final design. No FEM, PEEC, geometry optimization or temperature solution.\n\nInputs rationalized with tolerance 10^-12 before 50-digit evaluation. Area integrals independently check current and Joule power. JSON outputs rounded to machine precision; CSV reports complex radial current density.\n", "Text"];
  <|"result" -> result, "display" -> display, "reference_errors" -> errors, "environment" -> env|>
];
End[];
EndPackage[];
