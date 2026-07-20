import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests

# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "data\\coherence.xlsx"      # or coherence.xlsx / dai.xlsx
OUTPUT_FILE = INPUT_FILE.replace(".xlsx", "_mannwhitney.xlsx")

USE_FDR = False
ALPHA = 0.05
MIN_SUBJECTS = 3

# ============================================================

bands = pd.ExcelFile(INPUT_FILE).sheet_names
writer = pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl")

for band in bands:

    df = pd.read_excel(INPUT_FILE, sheet_name=band)

    group_col = "group" if "group" in df.columns else "Group"
    subject_col = "subject" if "subject" in df.columns else "Subject"

    pair_cols = [
        c for c in df.columns
        if c not in [group_col, subject_col]
    ]

    results = []

    for stage in ["pre", "post"]:

        if stage == "pre":
            stage_df = df[~df[subject_col].astype(str).str.endswith("-post")]
        else:
            stage_df = df[df[subject_col].astype(str).str.endswith("-post")]

        apraxia = stage_df[stage_df[group_col] == "Apraxia"]
        non = stage_df[stage_df[group_col] == "Non-Apraxia"]

        for pair in pair_cols:

            a = apraxia[pair].dropna().values
            n = non[pair].dropna().values

            if len(a) < MIN_SUBJECTS or len(n) < MIN_SUBJECTS:
                continue

            try:
                U, p = mannwhitneyu(
                    a,
                    n,
                    alternative="two-sided"
                )
            except Exception:
                continue

            results.append({
                "Comparison": f"{stage.capitalize()} Apraxia vs Non-Apraxia",
                "Pair": pair,
                "N Apraxia": len(a),
                "N Non-Apraxia": len(n),
                "Median Apraxia": np.median(a),
                "Median Non-Apraxia": np.median(n),
                "Median Δ": np.median(a) - np.median(n),
                "U": U,
                "p": p
            })

    results = pd.DataFrame(results)

    if results.empty:
        results.to_excel(writer, sheet_name=band, index=False)
        print(f"{band}: No valid tests.")
        continue

    results["FDR p"] = np.nan
    results["Significant"] = False

    for comparison in results["Comparison"].unique():

        mask = results["Comparison"] == comparison

        reject, p_adj, _, _ = multipletests(
            results.loc[mask, "p"],
            alpha=ALPHA,
            method="fdr_bh"
        )

        results.loc[mask, "FDR p"] = p_adj
        results.loc[mask, "Significant"] = reject

    results.to_excel(writer, sheet_name=band, index=False)

    print("\n" + "=" * 65)
    print(band.upper())
    print("=" * 65)

    for comparison in results["Comparison"].unique():

        print(f"\n{comparison}")

        sig = (
            results[
                (results["Comparison"] == comparison)
                & (results["Significant"] if USE_FDR else results["p"] < ALPHA)
            ]
            .sort_values("FDR p")
        )

        if sig.empty:
            print("  No significant connections.")
            continue

        for _, row in sig.iterrows():
            print(
                f"{row['Pair']:<12}"
                f" U={row['U']:.1f}"
                f"  p={row['p']:.4g}"
                f"  FDR={row['FDR p']:.4g}"
                f"  Δ={row['Median Δ']:.4f}"
                f"  N={int(row['N Apraxia'])}/{int(row['N Non-Apraxia'])}"
            )

writer.close()

print(f"\nResults saved to {OUTPUT_FILE}")