import pandas as pd
import numpy as np
from scipy.stats import ttest_rel
from statsmodels.stats.multitest import multipletests

# ============================================================
# ======================= SETTINGS ============================
# ============================================================

INPUT_FILE = "data\\coherence.xlsx"          # Change to coherence.xlsx or dai.xlsx if desired
OUTPUT_FILE = INPUT_FILE.replace(".xlsx", "_paired_t.xlsx")

USE_FDR = False
ALPHA = 0.05
MIN_PAIRS = 3

# ============================================================
# ========================= MAIN ==============================
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

    subjects = {
        subject: row
        for subject, row in df.set_index(subject_col).iterrows()
    }

    pre_subjects = [
        s for s in subjects
        if (not str(s).endswith("-post"))
        and (not str(s).startswith("CONTROL"))
    ]

    results = []

    for pair in pair_cols:

        pre = []
        post = []

        for subj in pre_subjects:

            post_subj = f"{subj}-post"

            if post_subj not in subjects:
                continue

            pre_val = subjects[subj][pair]
            post_val = subjects[post_subj][pair]

            if pd.isna(pre_val) or pd.isna(post_val):
                continue

            pre.append(pre_val)
            post.append(post_val)

        if len(pre) < MIN_PAIRS:
            continue

        try:
            t_stat, p = ttest_rel(post, pre, nan_policy="omit")
        except Exception:
            continue

        results.append({
            "Pair": pair,
            "N": len(pre),
            "Mean Pre": np.mean(pre),
            "Mean Post": np.mean(post),
            "Mean Δ": np.mean(np.array(post) - np.array(pre)),
            "t": t_stat,
            "p": p
        })

    results = pd.DataFrame(results)

    if len(results) == 0:
        results.to_excel(writer, sheet_name=band, index=False)
        print(f"{band}: No valid tests.")
        continue

    reject, p_fdr, _, _ = multipletests(
        results["p"],
        alpha=ALPHA,
        method="fdr_bh"
    )

    results["FDR p"] = p_fdr
    results["Significant"] = reject

    results.to_excel(writer, sheet_name=band, index=False)

    print("\n" + "=" * 60)
    print(band.upper())
    print("=" * 60)

    sig = results[results["Significant"]] if USE_FDR else results[results["p"] < ALPHA]

    if sig.empty:
        print("No significant connections.")
    else:
        for _, row in sig.sort_values("FDR p").iterrows():
            print(
                f"{row['Pair']:<12}"
                f"N={int(row['N'])}  "
                f"Δ={row['Mean Δ']:.4f}  "
                f"t={row['t']:.3f}  "
                f"p={row['p']:.4g}  "
                f"FDR={row['FDR p']:.4g}"
            )

writer.close()

print(f"\nResults saved to {OUTPUT_FILE}")