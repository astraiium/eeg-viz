import pandas as pd
import os

class DataManager:

    def __init__(self, config):

        paths = config["paths"]
        data_cfg = config.get("data", {})

        self.meta_columns = data_cfg.get("meta_columns", ["subject", "group"])
        self.pair_separator = data_cfg.get("pair_separator", "-")

        base = paths.get("data_dir", "")
        
        self.info_book = pd.read_excel(
            os.path.join(base, paths["subject_info_file"]),
        )

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

        alpha_sheet = self.coherence_book["gamma"]

        subjects = (
            alpha_sheet["subject"]
            .dropna()
            .astype(str)
            .tolist()
        )

        print(subjects)

        return subjects

    def get_connections(self, subject, metric, band):

        if metric == "Coherence":
            sheet = self.coherence_book[band.lower()]
        elif metric == "PLV":
            sheet = self.plv_book[band.lower()]
        elif metric == "DAI":
            sheet = self.dai_book[band.lower()]
        elif metric == "Aperiodic":
            sheet = self.aperiodic_book[band.lower()]

        # remove empty subject rows
        sheet = sheet.dropna(subset=["subject"])
        row = sheet[sheet["subject"].astype(str) == str(subject)]

        if row.empty:
            return {}

        row = row.iloc[0]

        connections = {}

        for col in sheet.columns:
            if col in self.meta_columns:
                continue

            value = row[col]

            if pd.isna(value):
                continue

            ch1, ch2 = col.split(self.pair_separator)

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
    
    def get_electrode_series(self, subject, electrodes):
        df = self.aperiodic_book["alpha"]

        row = df[df["subject"] == subject]

        if row.empty:
            return [None for _ in electrodes]

        row = row.iloc[0]

        values = []

        for e in electrodes:
            values.append(
                row.get(e, None)
            )

        return values
    
    def get_subject_info(self, subject):
        info_sheet = self.info_book

        row = info_sheet[info_sheet["Subject"] == subject]

        if row.empty:
            return {}

        row = row.iloc[0]

        info = {}

        for col in info_sheet.columns:
            value = row[col]

            # skip empty cells
            if pd.notna(value) and str(value).strip() != "":
                info[col] = value

        return info
