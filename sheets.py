import pandas as pd
import os

# ============================================================
# CONFIG
# ============================================================

WORKBOOK = "data//aperiodic.xlsx"      # Change as needed
PAIR_SEPARATOR = "-"
META_COLUMNS = {"subject", "group"}

# ============================================================

def canonical_pair(col):
    """
    Returns a canonical representation of a pair.
    Example:
        F3-C3 -> C3-F3
        T5-F7 -> F7-T5
    """
    if PAIR_SEPARATOR not in col:
        return col

    a, b = col.split(PAIR_SEPARATOR, 1)

    if a <= b:
        return f"{a}{PAIR_SEPARATOR}{b}"
    else:
        return f"{b}{PAIR_SEPARATOR}{a}"


print(f"Loading {WORKBOOK}...")

book = pd.read_excel(WORKBOOK, sheet_name=None)

new_book = {}

for sheet_name, df in book.items():

    print(f"\nProcessing sheet: {sheet_name}")

    out = df[list(df.columns[df.columns.isin(META_COLUMNS)])].copy()

    processed = set()

    for col in df.columns:

        if col in META_COLUMNS:
            continue

        if col in processed:
            continue

        canon = canonical_pair(col)

        if canon == col:
            reverse = None
            a, b = col.split(PAIR_SEPARATOR)
            reverse = f"{b}{PAIR_SEPARATOR}{a}"
        else:
            reverse = col

        if canon in df.columns:
            values = df[canon].copy()
            processed.add(canon)
        else:
            values = pd.Series([pd.NA] * len(df), index=df.index)

        if reverse in df.columns:
            values = values.combine_first(df[reverse])
            processed.add(reverse)

        out[canon] = values

    new_book[sheet_name] = out

with pd.ExcelWriter(WORKBOOK, engine="openpyxl") as writer:
    for sheet_name, df in new_book.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print("\nDone! Workbook updated.")