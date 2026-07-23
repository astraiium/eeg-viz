"""Web-ready backend API for the EEG visualization.

This module has NO PyQt dependency. Every method returns plain,
JSON-serializable Python objects (dicts / lists / numbers / strings),
so it can sit behind any web framework (stdlib http.server, Flask,
FastAPI, ...) and feed a browser front-end.

The desktop PyQt GUI talks to DataManager directly; the browser
front-end talks to this class. Both share the same core
(DataManager + colors), so the two front-ends stay consistent.

Typical usage from a web handler:

    backend = EEGBackend(load_config())
    payload = backend.compare("AA", "AG", "Coherence", "Alpha")
    return json.dumps(payload)
"""

from data_manager import DataManager
from colors import value_to_hex, difference_to_hex


class EEGBackend:

    def __init__(self, config, data=None):
        self.config = config
        # Reuse an existing DataManager (e.g. the desktop GUI's) when given,
        # so the workbooks are only loaded once.
        self.data = data if data is not None else DataManager(config)

    # ------------------------------------------------------------------
    # Catalog / dropdown options
    # ------------------------------------------------------------------

    def subjects(self):
        """List of patient/subject ids available for selection."""
        return self.data.get_subjects()

    def metrics(self):
        return self.config.get("metrics", {}).get("options", ["Coherence", "PLV", "DAI", "Aperiodic"])

    def bands(self):
        return self.config.get("bands", {}).get(
            "options", ["Alpha", "Beta", "Delta", "Theta", "Gamma"]
        )

    def defaults(self):
        return {
            "metric": self.config.get("metrics", {}).get("default"),
            "band": self.config.get("bands", {}).get("default"),
        }

    def options(self):
        """Everything a front-end needs to build its selectors at once."""
        return {
            "subjects": self.subjects(),
            "metrics": self.metrics(),
            "bands": self.bands(),
            "defaults": self.defaults(),
            "coherence_plot": self.coherence_plot_config()
        }

    # ------------------------------------------------------------------
    # Head geometry / layout (static; depends only on config)
    # ------------------------------------------------------------------

    def head_layout(self):
        """Electrode positions, lobe groups, and head outline geometry."""
        appearance = self.config["appearance"]
        head = appearance["head"]

        # Map each electrode to its lobe so the front-end can color it.
        electrode_lobe = {}
        lobes = {}
        for lobe, cfg in self.config["lobes"].items():
            lobes[lobe] = {
                "color": cfg["color"],
                "electrodes": list(cfg["electrodes"]),
                "visible": cfg.get("visible", True),
            }
            for electrode in cfg["electrodes"]:
                electrode_lobe[electrode] = lobe

        electrodes = []
        for name, (x, y) in self.config["electrode_positions"].items():
            lobe = electrode_lobe.get(name)
            electrodes.append({
                "name": name,
                "x": x,
                "y": y,
                "lobe": lobe,
                "color": lobes.get(lobe, {}).get("color", "#FFFFFF"),
            })

        return {
            "radius": head["radius"],
            "background": appearance.get("background", "#000000"),
            "electrode_diameter": appearance.get("electrode", {}).get("diameter", 25),
            "connection_curvature": appearance.get("connection", {}).get("curvature", 0.25),
            "nose": {
                "width": head.get("nose_width", 60),
                "height": head.get("nose_height", 45),
            },
            "ear_radius": head.get("ear_radius", 28),
            "lobes": lobes,
            "electrodes": electrodes,
        }

    # ------------------------------------------------------------------
    # Connectivity data
    # ------------------------------------------------------------------

    def connectivity(self, subject, metric, band):
        """Connections for a single patient, with precomputed colors."""
        raw = self.data.get_connections(subject, metric, band)

        connections = [
            {
                "source": a,
                "target": b,
                "value": value,
                "color": value_to_hex(value, metric),
            }
            for (a, b), value in raw.items()
        ]

        return {
            "subject": subject,
            "metric": metric,
            "band": band,
            "connections": connections,
        }

    def compare(self, subject_a, subject_b, metric, band):
        """Side-by-side payload for two patients under the same metric/band."""
        return {
            "metric": metric,
            "band": band,
            "left": self.connectivity(subject_a, metric, band),
            "right": self.connectivity(subject_b, metric, band),
        }
        
    def difference(self, subject_a, subject_b, metric, band):
        raw_a = self.data.get_connections(subject_a, metric, band)
        raw_b = self.data.get_connections(subject_b, metric, band)

        pairs = set(raw_a.keys()) | set(raw_b.keys())

        diffs = {
            pair: raw_b.get(pair, 0) - raw_a.get(pair, 0)
            for pair in pairs
        }

        max_diff = max(abs(v) for v in diffs.values()) if diffs else 1

        connections = []

        for (a, b), diff in diffs.items():
            connections.append({
                "source": a,
                "target": b,
                "value": diff,
                "color": difference_to_hex(diff, max_diff)
            })

        return {
            "mode": "difference",
            "subject_a": subject_a,
            "subject_b": subject_b,
            "metric": metric,
            "band": band,
            "connections": connections
        }

    # ------------------------------------------------------------------
    # Frontal-Central coherence line plot
    # ------------------------------------------------------------------

    def coherence_plot_config(self):
        """Static config a front-end needs to build the line-plot controls."""
        cfg = self.config.get("coherence_plot", {})
        return {
            "title": cfg.get("title", "Coherence Plots"),
            "defaults": cfg.get("defaults", {}),
            "series": cfg.get("series", {}),
            "groups": [g["name"] for g in cfg.get("groups", [])],
        }

    def coherence_line_plot(self, pre, post, metric, band, control=None):
        """Data for the pre/post/control coherence line plot.

        Returns one entry per group (e.g. Left / Right Frontal-Central),
        each with the x-axis pair labels and the three series' values.
        JSON-serializable.
        """
        cfg = self.config.get("coherence_plot", {})
        defaults = cfg.get("defaults", {})
        control = control or defaults.get("control_subject", "CONTROL_AVG")

        groups = []
        for group in cfg.get("groups", []):
            pairs = group["pairs"]
            groups.append({
                "name": group["name"],
                "pairs": pairs,
                "pre": self.data.get_metric_series(pre, metric, band, pairs),
                "post": self.data.get_metric_series(post, metric, band, pairs),
                "control": self.data.get_metric_series(control, metric, band, pairs)
            })

        return {
            "title": cfg.get("title", "Frontal-Central Coherence Plots"),
            "band": band,
            "subjects": {"pre": pre, "post": post, "control": control},
            "series": cfg.get("series", {}),
            "groups": groups,
        }
