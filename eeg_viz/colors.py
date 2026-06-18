"""Framework-agnostic color mapping for connectivity values.

Pure functions with no PyQt dependency, so the desktop (PyQt) front-end
and the web backend share a single source of truth for how a metric
value maps to a color.

- Coherence: 0 -> 1, sequential scale (purple -> blue -> green -> yellow -> red)
- DAI:      -1 -> +1, diverging scale (blue -> white -> red)
"""

import colorsys


def _coherence_rgb(value):
    v = max(0.0, min(1.0, float(value)))
    hue = (1 - v) * 270.0  # degrees: 270 (purple) at 0, 0 (red) at 1
    r, g, b = colorsys.hsv_to_rgb((hue % 360) / 360.0, 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))


def _dai_rgb(value):
    v = max(-1.0, min(1.0, float(value)))
    t = (v + 1) / 2  # normalize to 0..1

    if t < 0.5:
        c = int(255 * (t / 0.5))   # blue -> white
        return (c, c, 255)
    else:
        c = int(255 * (1 - (t - 0.5) / 0.5))  # white -> red
        return (255, c, c)


def value_to_rgb(value, metric):
    """Return an (r, g, b) tuple (0-255) for a value under the given metric."""
    if value is None:
        return (200, 200, 200)

    if metric == "Coherence":
        return _coherence_rgb(value)
    return _dai_rgb(value)


def value_to_hex(value, metric):
    """Return a "#RRGGBB" string for a value under the given metric."""
    r, g, b = value_to_rgb(value, metric)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)
