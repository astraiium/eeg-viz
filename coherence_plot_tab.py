"""Frontal-Central coherence line-plot tab.

Reproduces the pre / post / control coherence comparison (see
image_sample/front_central_delta_left_vs_right.png): one subplot per
group (Left / Right Frontal-Central), each plotting three series across
a set of channel pairs.

The plot data comes from EEGBackend.coherence_line_plot(), so this tab
and any future web front-end draw the exact same numbers.
"""

import math

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel
)

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure


def _nan_safe(values):
    """Convert None -> NaN so matplotlib leaves a gap instead of erroring."""
    return [float("nan") if v is None else v for v in values]


class CoherencePlotTab(QWidget):

    def __init__(self, backend):
        super().__init__()

        self.backend = backend
        self.plot_cfg = backend.coherence_plot_config()
        defaults = self.plot_cfg.get("defaults", {})

        subjects = backend.subjects()
        bands = backend.bands()

        layout = QVBoxLayout()
        self.setLayout(layout)

        # -------------------------
        # Selectors
        # -------------------------

        controls = QHBoxLayout()

        self.pre_dropdown = self._make_selector(
            controls, "Pre subject", subjects, defaults.get("pre_subject"))
        self.post_dropdown = self._make_selector(
            controls, "Post subject", subjects, defaults.get("post_subject"))
        self.control_dropdown = self._make_selector(
            controls, "Control", subjects, defaults.get("control_subject"))
        self.band_dropdown = self._make_selector(
            controls, "Band", bands, defaults.get("band"))

        controls.addStretch()
        layout.addLayout(controls)

        # -------------------------
        # Matplotlib canvas
        # -------------------------

        self.figure = Figure(figsize=(11, 4.5), constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(NavigationToolbar(self.canvas, self))
        layout.addWidget(self.canvas)

        for dropdown in (self.pre_dropdown, self.post_dropdown,
                         self.control_dropdown, self.band_dropdown):
            dropdown.currentTextChanged.connect(self.redraw)

        self.redraw()

    def _make_selector(self, parent_layout, label, items, default):
        parent_layout.addWidget(QLabel(label + ":"))
        combo = QComboBox()
        combo.addItems(items)
        if default and default in items:
            combo.setCurrentText(default)
        parent_layout.addWidget(combo)
        return combo

    def redraw(self):
        pre = self.pre_dropdown.currentText()
        post = self.post_dropdown.currentText()
        control = self.control_dropdown.currentText()
        band = self.band_dropdown.currentText()

        data = self.backend.coherence_line_plot(pre, post, band, control)
        series = data["series"]
        groups = data["groups"]

        pre_style = series.get("pre", {})
        post_style = series.get("post", {})
        ctrl_style = series.get("control", {})

        # Common y-limit across all subplots, with headroom, so the shared
        # axis doesn't clip a peak that lives in another group.
        all_values = [
            v
            for group in groups
            for key in ("pre", "post", "control")
            for v in group[key]
            if v is not None and not math.isnan(v)
        ]
        y_top = (max(all_values) * 1.12) if all_values else 1.0

        # Lay the groups out in a grid (2 columns) so adding groups grows
        # downward instead of squeezing everything into one row.
        n = len(groups)
        ncols = 1 if n <= 1 else 2
        nrows = math.ceil(n / ncols)

        self.figure.clear()
        self.figure.set_size_inches(11, max(4.5, 3.2 * nrows), forward=True)
        axes = self.figure.subplots(
            nrows, ncols, sharey=True, squeeze=False).flatten()

        for ax, group in zip(axes, groups):
            x = list(range(len(group["pairs"])))

            # Legend labels are the actual subjects chosen in the dropdowns.
            ax.plot(x, _nan_safe(group["control"]), marker="o", markersize=4,
                    linewidth=1.3, color=ctrl_style.get("color", "#999999"),
                    label=control)
            ax.plot(x, _nan_safe(group["pre"]), marker="o", markersize=4,
                    linewidth=1.6, color=pre_style.get("color", "#D62728"),
                    label=pre)
            ax.plot(x, _nan_safe(group["post"]), marker="o", markersize=4,
                    linewidth=1.6, color=post_style.get("color", "#2CA02C"),
                    label=post)

            ax.set_title(f"{band.upper()} - {group['name']}", fontsize=10)
            ax.set_xticks(x)
            ax.set_xticklabels(group["pairs"], rotation=45, ha="right", fontsize=8)
            ax.set_xlabel("Channel Pairs", fontsize=9)
            ax.set_ylim(0, y_top)
            ax.grid(True, axis="x", linestyle=":", alpha=0.4)
            ax.legend(fontsize=8, loc="upper right")
            ax.set_ylabel("Coherence", fontsize=9)

        # Hide any unused cells in the last row.
        for ax in axes[n:]:
            ax.set_visible(False)

        self.figure.suptitle(
            f"{data['title']}  —  {pre} (pre) vs {post} (post)",
            fontsize=13
        )

        self.canvas.draw_idle()
