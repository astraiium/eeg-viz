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
        
        self.plv_book = pd.read_excel(
            paths["plv_file"],
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
        elif metric == "PLV":
            sheet = self.plv_book[band.lower()]
        elif metric == "DAI":
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


    def get_metric_series(self, subject, metric, band, pairs):
        """
        Return metric values for `subject`/`band` aligned to `pairs`.
        """
        connections = self.get_connections(subject, metric, band)

        values = []

        for pair in pairs:
            a, b = pair.split(self.pair_separator)

            values.append(
                connections.get((a, b),
                    connections.get((b, a)))
            )

        return values
