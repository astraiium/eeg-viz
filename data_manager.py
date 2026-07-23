import pandas as pd
import os

class DataManager:

    def __init__(self, config):

        paths = config["paths"]
        data_cfg = config.get("data", {})

        self.meta_columns = data_cfg.get("meta_columns", ["subject", "group"])
        self.pair_separator = data_cfg.get("pair_separator", "-")

        base = paths.get("data_dir", "")

        self.coherence_book = pd.read_excel(
            os.path.join(base, paths["coherence_file"]),
            sheet_name=None
        )

        self.plv_book = pd.read_excel(
            os.path.join(base, paths["plv_file"]),
            sheet_name=None
        )

        self.dai_book = pd.read_excel(
            os.path.join(base, paths["dai_file"]),
            sheet_name=None
        )

        self.aperiodic_book = pd.read_excel(
            os.path.join(base, paths["aperiodic_file"]),
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
        elif metric == "Aperiodic":
            sheet = self.aperiodic_book[
                list(self.aperiodic_book.keys())[0]
            ]

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
    
    def get_electrode_values(self, subject, metric):
            """
            Get single-electrode metric values (e.g. Aperiodic exponent).

            Returns:
                {
                    "C3": 1.52,
                    "F3": 1.84,
                    ...
                }
            """

            if metric == "Aperiodic":
                sheet = self.aperiodic_book[
                    list(self.aperiodic_book.keys())[0]
                ]
            else:
                return {}

            row = sheet[sheet["subject"] == subject]

            if row.empty:
                return {}

            row = row.iloc[0]

            values = {}

            for col in sheet.columns:

                # Skip metadata columns
                if col in self.meta_columns:
                    continue

                value = row[col]

                if pd.isna(value):
                    continue

                values[col] = float(value)

            return values


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
