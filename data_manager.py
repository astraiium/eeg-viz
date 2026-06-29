import pandas as pd


class DataManager:

    def __init__(self, config):

        paths = config["paths"]
        data_cfg = config.get("data", {})

        self.meta_columns = data_cfg.get("meta_columns", ["subject", "group"])
        self.pair_separator = data_cfg.get("pair_separator", "-")

        self.coherence_book = pd.read_excel(
            paths["coherence_file"],
            sheet_name=None
        )

        self.dai_book = pd.read_excel(
            paths["dai_file"],
            sheet_name=None
        )

    def get_subjects(self):

        alpha_sheet = self.coherence_book["alpha"]
        print(alpha_sheet["subject"].tolist())
        return alpha_sheet["subject"].tolist()

    def get_connections(self, subject, metric, band):

        if metric == "Coherence":
            sheet = self.coherence_book[band.lower()]
        else:
            sheet = self.dai_book[band.lower()]

        row = sheet[sheet["subject"] == subject]

        if row.empty:
            return {}

        row = row.iloc[0]

        connections = {}

        for col in sheet.columns:

            if col in self.meta_columns:
                continue

            ch1, ch2 = col.split(self.pair_separator)

            value = row[col]

            if pd.isna(value):
                continue

            connections[(ch1, ch2)] = float(value)

        return connections

    def get_coherence_series(self, subject, band, pairs):
        """Return coherence values for `subject`/`band` aligned to `pairs`.

        Each pair is a string like "C3-F3". The connectivity matrix only
        stores each pair once, so we try both column orders ("C3-F3" and
        "F3-C3") and take whichever holds a real (non-NaN) value. Missing
        pairs come back as None so the caller can leave a gap in the line.
        """
        sheet = self.coherence_book[band.lower()]

        match = sheet[sheet["subject"] == subject]
        if match.empty:
            return [None] * len(pairs)

        row = match.iloc[0]
        values = []

        for pair in pairs:
            a, b = pair.split(self.pair_separator)
            value = None

            for col in (pair, b + self.pair_separator + a):
                if col in sheet.columns and not pd.isna(row[col]):
                    value = float(row[col])
                    break

            values.append(value)

        return values
