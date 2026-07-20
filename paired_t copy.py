import pandas as pd
import numpy as np
from scipy.stats import ttest_rel
from statsmodels.stats.multitest import multipletests


# ============================================================
# ======================= SETTINGS ============================
# ============================================================

METRICS = {
    "Coherence": "data\\coherence.xlsx",
    "PLV": "data\\plv.xlsx",
    # Add more here:
    # "Aperiodic": "data/aperiodic_slope.xlsx",
    # "Power": "data/power.xlsx"
}

OUTPUT_FILE = "metric_convergence_results.xlsx"

ALPHA = 0.05
MIN_PAIRS = 3

USE_FDR = False


# ============================================================
# =============== PAIRED T TEST FUNCTION =====================
# ============================================================

def run_paired_ttest(filename, metric_name):

    excel = pd.ExcelFile(filename)

    metric_results = []

    for band in excel.sheet_names:

        df = pd.read_excel(filename, sheet_name=band)

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
                t_stat, p = ttest_rel(
                    post,
                    pre,
                    nan_policy="omit"
                )

            except Exception:
                continue


            delta = np.mean(
                np.array(post) - np.array(pre)
            )


            metric_results.append({

                "Metric": metric_name,
                "Band": band,
                "Pair": pair,

                "N": len(pre),

                "Mean Pre": np.mean(pre),
                "Mean Post": np.mean(post),

                "Delta": delta,

                "t": t_stat,
                "p": p
            })


    return pd.DataFrame(metric_results)



# ============================================================
# ======================= RUN TESTS ===========================
# ============================================================


all_results = []


for metric, file in METRICS.items():

    print(f"Running {metric}...")

    result = run_paired_ttest(
        file,
        metric
    )

    all_results.append(result)



combined = pd.concat(
    all_results,
    ignore_index=True
)



# ============================================================
# ================= MULTIPLE COMPARISON ======================
# ============================================================


combined["FDR p"] = np.nan
combined["Significant"] = False


for metric in combined["Metric"].unique():

    idx = combined["Metric"] == metric

    reject, p_fdr, _, _ = multipletests(
        combined.loc[idx, "p"],
        alpha=ALPHA,
        method="fdr_bh"
    )

    combined.loc[idx, "FDR p"] = p_fdr
    combined.loc[idx, "Significant"] = reject



# ============================================================
# =============== CONVERGENCE ANALYSIS =======================
# ============================================================


summary = []


for (band, pair), group in combined.groupby(
        ["Band", "Pair"]
):

    total_metrics = len(group)

    sig = group[group["Significant"]] \
        if USE_FDR \
        else group[group["p"] < ALPHA]


    sig_count = len(sig)


    deltas = sig["Delta"].values


    if sig_count > 0:

        if np.all(deltas > 0):
            direction = "Increase"

        elif np.all(deltas < 0):
            direction = "Decrease"

        else:
            direction = "Mixed"

    else:
        direction = "None"



    summary.append({

        "Band": band,
        "Pair": pair,

        "Metrics Tested": total_metrics,

        "Significant Metrics": sig_count,

        "Convergence Score":
            sig_count / total_metrics,

        "Direction":
            direction
    })



summary = pd.DataFrame(summary)



# ============================================================
# ================= IMPORTANT CONNECTIONS ====================
# ============================================================

MIN_SIGNIFICANT_METRICS = 2
TOTAL_EXPECTED_METRICS = 2

important = summary[
    (summary["Significant Metrics"] >= MIN_SIGNIFICANT_METRICS)
    &
    (summary["Metrics Tested"] == TOTAL_EXPECTED_METRICS)
]


# ============================================================
# ======================= SAVE FILE ==========================
# ============================================================


with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    combined.to_excel(
        writer,
        sheet_name="All Metric Tests",
        index=False
    )

    summary.to_excel(
        writer,
        sheet_name="Convergence Summary",
        index=False
    )

    important.to_excel(
        writer,
        sheet_name="All Metrics Significant",
        index=False
    )


# ============================================================
# ======================= PRINT ==============================
# ============================================================


print("\n" + "="*70)
print("CONNECTIONS SIGNIFICANT ACROSS ALL METRICS")
print("="*70)


if len(important) == 0:

    print("No fully convergent connections found.")

else:

    for _, row in important.iterrows():

        print(
            f"{row['Band']:8s} "
            f"{row['Pair']:15s} "
            f"{row['Direction']:10s} "
            f"{int(row['Significant Metrics'])}/"
            f"{int(row['Metrics Tested'])}"
        )


print("\nSaved:", OUTPUT_FILE)