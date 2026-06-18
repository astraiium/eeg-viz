from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsTextItem
)

from PyQt6.QtGui import QBrush, QColor, QPen, QPainterPath
from PyQt6.QtCore import Qt

import math

from colors import value_to_rgb


class ElectrodeItem(QGraphicsEllipseItem):

    def __init__(self, name, x, y, color, parent_map, style):

        diameter = style["diameter"]
        offset = diameter / 2

        super().__init__(x - offset, y - offset, diameter, diameter)

        self.name = name
        self.active = True
        self.default_color = color
        self.inactive_color = QColor(style["inactive_color"])
        self.parent_map = parent_map

        self.setZValue(2)

        self.setBrush(QBrush(color))
        pen = QPen(QColor(style["outline_color"]))
        pen.setWidthF(style["outline_width"])
        self.setPen(pen)

    def mousePressEvent(self, event):

        self.active = not self.active

        if self.active:
            self.setBrush(QBrush(self.default_color))
        else:
            self.setBrush(QBrush(self.inactive_color))

        # redraw connections whenever toggled
        self.parent_map.redraw()

        super().mousePressEvent(event)


class ElectrodeMap(QGraphicsView):

    def __init__(self, config):
        super().__init__()

        appearance = config["appearance"]
        electrode_style = appearance["electrode"]
        head_style = appearance["head"]
        connection_style = appearance["connection"]

        self.curvature = connection_style["curvature"]
        self.connection_width = connection_style["width"]

        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QColor(appearance["background"]))
        self.setScene(self.scene)

        self.setRenderHint(self.renderHints())

        self.electrodes = {}
        self.connection_items = []
        self.connections = {}
        self.metric = config.get("metrics", {}).get("default", "Coherence")

        # Build lobe membership, colors and visibility from config.
        self.lobe_map = {}
        self.active_lobes = {}
        lobe_colors = {}

        for lobe, lobe_cfg in config["lobes"].items():
            self.lobe_map[lobe] = set(lobe_cfg["electrodes"])
            self.active_lobes[lobe] = lobe_cfg.get("visible", True)
            lobe_colors[lobe] = QColor(lobe_cfg["color"])

        # Map each electrode to its lobe color via the positions table.
        electrode_to_lobe = {}
        for lobe, members in self.lobe_map.items():
            for name in members:
                electrode_to_lobe[name] = lobe

        # Head outline.
        radius = head_style["radius"]
        head = self.scene.addEllipse(
            -radius, -radius, radius * 2, radius * 2
        )

        pen = QPen(QColor(head_style["outline_color"]))
        pen.setWidthF(head_style["outline_width"])

        head.setPen(pen)
        head.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        head.setZValue(0)

        # Nose and ears (orientation markers), drawn with the same pen.
        self.draw_head_features(radius, head_style, pen)

        # Electrodes.
        for name, (x, y) in config["electrode_positions"].items():

            lobe = electrode_to_lobe.get(name)
            color = lobe_colors.get(lobe, QColor("#FFFFFF"))

            electrode = ElectrodeItem(
                name,
                x,
                y,
                color,
                self,
                electrode_style
            )

            self.scene.addItem(electrode)
            self.electrodes[name] = electrode

            label = QGraphicsTextItem(name)
            label.setDefaultTextColor(QColor(electrode_style["label_color"]))
            self.scene.addItem(label)

            rect = label.boundingRect()

            label.setPos(
                x - rect.width() / 2,
                y + 12
            )

        self.redraw()

        # Remember the content extent so the view can scale to fit it
        # (important when two maps share a window side by side).
        self._fit_rect = self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, "_fit_rect", None) is not None:
            self.fitInView(self._fit_rect, Qt.AspectRatioMode.KeepAspectRatio)

    def draw_head_features(self, radius, head_style, pen):
        """Draw the nose (top) and ears (sides) of the head outline.

        Scene y points downward, so the top of the head is at -radius.
        """

        # ----- Nose: triangle at the top, pointing outward (up) -----
        nose_w = head_style.get("nose_width", 60)
        nose_h = head_style.get("nose_height", 45)

        half = nose_w / 2.0
        # Base corners sit on the rim; apex juts out past it.
        base_y = -math.sqrt(max(radius ** 2 - half ** 2, 0))
        apex = (0, -(radius + nose_h))

        nose = self._polyline_path([
            (-half, base_y),
            apex,
            (half, base_y),
        ])

        nose_item = self.scene.addPath(nose, pen)
        nose_item.setZValue(0)

        # ----- Ears: half circles bulging out on each side -----
        ear_r = head_style.get("ear_radius", 28)

        # Right ear: outer half (angles -90..90 deg around the rim point).
        right = self._semicircle_path(radius, 0, ear_r, -90, 90)
        # Left ear: outer half (angles 90..270 deg).
        left = self._semicircle_path(-radius, 0, ear_r, 90, 270)

        for ear in (right, left):
            ear_item = self.scene.addPath(ear, pen)
            ear_item.setZValue(0)

    @staticmethod
    def _polyline_path(points):
        path = QPainterPath()
        path.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            path.lineTo(x, y)
        return path

    def _semicircle_path(self, cx, cy, r, start_deg, end_deg, steps=24):
        """Build an open semicircle arc centered at (cx, cy)."""
        points = []
        for i in range(steps + 1):
            t = math.radians(start_deg + (end_deg - start_deg) * i / steps)
            points.append((cx + r * math.cos(t), cy + r * math.sin(t)))
        return self._polyline_path(points)

    def set_connections(self, connections, metric="Coherence"):
        self.connections = connections
        self.metric = metric
        self.redraw()

    def electrode_visible(self, name):

        for lobe, electrodes in self.lobe_map.items():
            if name in electrodes:
                return self.active_lobes[lobe]

        return False

    def toggle_lobe(self, lobe, state: bool):
        self.active_lobes[lobe] = state
        self.redraw()

    # ----------------------------
    # redraw system
    # ----------------------------

    def redraw(self):
        self.clear_connections()
        self.draw_connections()

    def clear_connections(self):
        for item in self.connection_items:
            self.scene.removeItem(item)
        self.connection_items = []

    def draw_connections(self):
        for (a, b), value in self.connections.items():

            if a not in self.electrodes or b not in self.electrodes:
                continue

            e1 = self.electrodes[a]
            e2 = self.electrodes[b]

            if not (
            e1.active and e2.active and
            self.electrode_visible(a) and
            self.electrode_visible(b)
            ):
                continue

            p1 = e1.sceneBoundingRect().center()
            p2 = e2.sceneBoundingRect().center()

            x1, y1 = p1.x(), p1.y()
            x2, y2 = p2.x(), p2.y()

            # midpoint
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2

            # perpendicular offset (controls "curvature strength")
            dx = x2 - x1
            dy = y2 - y1

            # rotate vector 90 degrees
            offset = self.curvature  # curvature strength (from config)
            cx = mx - dy * offset
            cy = my + dx * offset

            path = QPainterPath()
            path.moveTo(x1, y1)
            path.quadTo(cx, cy, x2, y2)

            color = self.value_to_color(value)

            pen = QPen(color)
            pen.setWidthF(self.connection_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)

            item = self.scene.addPath(path, pen)
            item.setZValue(1)

            self.connection_items.append(item)

    def value_to_color(self, value):
        # Delegates to the shared, framework-agnostic color mapping so the
        # desktop and web front-ends render identical colors.
        r, g, b = value_to_rgb(value, self.metric)
        return QColor(r, g, b)
