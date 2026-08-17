import pandas as pd
import numpy as np

# ============================================================
# ======================= PARAMETERS ==========================
# ============================================================

INPUT_FILE = "data//dai.xlsx"
OUTPUT_FILE = "data//dai_corrected.xlsx"

BANDS = ["delta", "theta", "alpha", "beta", "gamma"]

# ============================================================
# =========================== MAIN ===========================
# ============================================================

def main():

    print(f"Reading: {INPUT_FILE}")

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:

        for band in BANDS:

            print(f"Processing {band}...")

            df = pd.read_excel(INPUT_FILE, sheet_name=band)

            # Columns containing DAI values
            # Exclude metadata columns
            metadata_cols = ["subject", "group"]
            dai_cols = [c for c in df.columns if c not in metadata_cols]

            # Flip DAI sign
            df[dai_cols] = df[dai_cols] * -1

            # Write corrected sheet
            df.to_excel(
                writer,
                sheet_name=band,
                index=False
            )

    print("\n[SUCCESS]")
    print(f"Corrected DAI workbook written to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()