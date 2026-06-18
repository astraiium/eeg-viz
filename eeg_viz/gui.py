from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QComboBox,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QTabWidget
)

from PyQt6.QtCore import Qt

from electrode_map import ElectrodeMap
from data_manager import DataManager
from backend import EEGBackend
from coherence_plot_tab import CoherencePlotTab


class EEGPanel(QWidget):
    """One patient view: a subject dropdown stacked above an electrode map.

    The panel owns its own ElectrodeMap; metric and band are pushed in from
    the parent window (shared across all panels) via set_metric_band().
    """

    def __init__(self, config, subjects, data_manager,
                 label="Patient", default_subject=None):
        super().__init__()

        self.data_manager = data_manager
        self._metric = None
        self._band = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QHBoxLayout()
        header.addWidget(QLabel(label + ":"))

        self.subject_dropdown = QComboBox()
        self.subject_dropdown.addItems(subjects)
        if default_subject:
            self.subject_dropdown.setCurrentText(default_subject)
        header.addWidget(self.subject_dropdown)
        header.addStretch()

        layout.addLayout(header)

        self.map = ElectrodeMap(config)
        layout.addWidget(self.map)

        self.subject_dropdown.currentTextChanged.connect(self.refresh)

    def set_metric_band(self, metric, band):
        self._metric = metric
        self._band = band
        self.refresh()

    def current_subject(self):
        return self.subject_dropdown.currentText()

    def refresh(self):
        if self._metric is None or self._band is None:
            return

        connections = self.data_manager.get_connections(
            self.current_subject(),
            self._metric,
            self._band
        )

        self.map.set_connections(connections, self._metric)


class MainWindow(QMainWindow):

    def __init__(self, config):
        super().__init__()

        self.config = config

        window_cfg = config.get("window", {})
        self.setWindowTitle(window_cfg.get("title", "EEG Vistool"))
        self.resize(
            window_cfg.get("width", 1000),
            window_cfg.get("height", 800)
        )

        self.data_manager = DataManager(config)
        # Backend shares the same DataManager (workbooks loaded once) and
        # powers the coherence plot tab — the same surface a web front-end uses.
        self.backend = EEGBackend(config, data=self.data_manager)
        subjects = self.data_manager.get_subjects()

        # -------------------------
        # Tabbed interface
        # -------------------------

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        comparison = QWidget()
        layout = QVBoxLayout()
        comparison.setLayout(layout)
        self.tabs.addTab(comparison, "Connectivity")

        # -------------------------
        # Lobe toggles (shared across both panels)
        # -------------------------

        self.lobe_layout = QHBoxLayout()
        self.lobe_layout.addWidget(QLabel("Lobes:"))
        layout.addLayout(self.lobe_layout)

        self.lobe_checkboxes = {}

        for lobe, lobe_cfg in config["lobes"].items():

            cb = QCheckBox(lobe.capitalize())
            cb.setChecked(lobe_cfg.get("visible", True))

            cb.stateChanged.connect(
                lambda state, l=lobe: self.toggle_lobe(l, state == 2)
            )

            self.lobe_layout.addWidget(cb)
            self.lobe_checkboxes[lobe] = cb

        self.lobe_layout.addStretch()

        # -------------------------
        # Metric + band selectors (shared, so the comparison is apples-to-apples)
        # -------------------------

        controls = QHBoxLayout()

        metrics_cfg = config.get("metrics", {})
        controls.addWidget(QLabel("Metric:"))
        self.metric_dropdown = QComboBox()
        self.metric_dropdown.addItems(
            metrics_cfg.get("options", ["Coherence", "DAI"])
        )
        if metrics_cfg.get("default"):
            self.metric_dropdown.setCurrentText(metrics_cfg["default"])
        controls.addWidget(self.metric_dropdown)

        bands_cfg = config.get("bands", {})
        controls.addWidget(QLabel("Band:"))
        self.band_dropdown = QComboBox()
        self.band_dropdown.addItems(
            bands_cfg.get("options", ["Alpha", "Beta", "Delta", "Theta", "Gamma"])
        )
        if bands_cfg.get("default"):
            self.band_dropdown.setCurrentText(bands_cfg["default"])
        controls.addWidget(self.band_dropdown)

        controls.addStretch()
        layout.addLayout(controls)

        # -------------------------
        # Two patient panels, side by side
        # -------------------------

        default_a = subjects[0] if subjects else None
        default_b = subjects[1] if len(subjects) > 1 else default_a

        self.panels = [
            EEGPanel(config, subjects, self.data_manager,
                     label="Patient A", default_subject=default_a),
            EEGPanel(config, subjects, self.data_manager,
                     label="Patient B", default_subject=default_b),
        ]

        panel_row = QHBoxLayout()
        for panel in self.panels:
            panel_row.addWidget(panel)
        layout.addLayout(panel_row)

        # -------------------------
        # Signals
        # -------------------------

        self.metric_dropdown.currentTextChanged.connect(self.update_all)
        self.band_dropdown.currentTextChanged.connect(self.update_all)

        # initial draw
        self.update_all()

        # -------------------------
        # Coherence plot tab
        # -------------------------

        self.coherence_tab = CoherencePlotTab(self.backend)
        self.tabs.addTab(self.coherence_tab, "Coherence Plot")

    def toggle_lobe(self, lobe, state: bool):
        for panel in self.panels:
            panel.map.toggle_lobe(lobe, state)

    def update_all(self):
        metric = self.metric_dropdown.currentText()
        band = self.band_dropdown.currentText()

        for panel in self.panels:
            panel.set_metric_band(metric, band)
