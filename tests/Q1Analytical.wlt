q1Root = If[ValueQ[stageRoot] && DirectoryQ[FileNameJoin[{stageRoot,"configs"}]], stageRoot, DirectoryName[DirectoryName[$InputFileName]]];
Get[FileNameJoin[{q1Root, "src", "Q1Analytical.wl"}]];
q1Inputs = Import[FileNameJoin[{q1Root, "configs", "reference_parameters.json"}], "RawJSON"];
q1Computed = LitzAnalytical`RoundWireSolution[q1Inputs];
q1Reference = Import[FileNameJoin[{q1Root, "configs", "reference_values.json"}], "RawJSON"]["values"];
VerificationTest[Abs[1000 q1Computed["delta_m"]/q1Reference["delta_mm"] - 1] < 10^-6, True, TestID -> "skin-depth-reference"]
VerificationTest[Abs[1000 q1Computed["Rdc_ohm_per_m"]/q1Reference["Q1_Rdc_mohm_per_m"] - 1] < 10^-6, True, TestID -> "dc-resistance-reference"]
VerificationTest[Abs[1000 q1Computed["Rac_ohm_per_m"]/q1Reference["Q1_Rac_mohm_per_m"] - 1] < 10^-6, True, TestID -> "ac-resistance-reference"]
VerificationTest[Abs[1000 q1Computed["Xinternal_ohm_per_m"]/q1Reference["Q1_Xint_mohm_per_m"] - 1] < 10^-6, True, TestID -> "internal-reactance-reference"]
VerificationTest[Abs[q1Computed["Rac_Rdc"]/q1Reference["Q1_Rac_Rdc"] - 1] < 10^-6, True, TestID -> "ac-dc-ratio-reference"]
VerificationTest[Abs[q1Computed["loss_W_per_m"]/q1Reference["Q1_P_W_per_m"] - 1] < 10^-6, True, TestID -> "RMS-loss-reference"]
VerificationTest[q1Computed["current_integral_relative_error"] < 10^-8, True, TestID -> "complex-current-integral"]
VerificationTest[q1Computed["power_integral_relative_error"] < 10^-8, True, TestID -> "joule-power-integral"]
VerificationTest[Abs[q1Computed["low_frequency_Rac_Rdc"] - 1] < 10^-8, True, TestID -> "positive-low-frequency-limit"]
VerificationTest[q1Computed["Rac_ohm_per_m"] >= q1Computed["Rdc_ohm_per_m"] && q1Computed["Xinternal_ohm_per_m"] > 0, True, TestID -> "passivity-and-phasor-sign"]
VerificationTest[Abs[q1Computed["loss_W_per_m"]/(q1Inputs["current_RMS_A"]^2 q1Computed["Rac_ohm_per_m"]) - 1] < 10^-12, True, TestID -> "RMS-no-extra-half"]
VerificationTest[q1Computed["Jdc_A_per_m2"]/10^6 > 4, True, TestID -> "Q1-current-density-conflict-retained"]
