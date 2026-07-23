import colorsys
import math

METRIC_RANGES = {
    "Coherence": (0, 1),
    "PLV": (0, 1),
    "DAI": (-1, 1),
    "Aperiodic": (-0.3, 3)
}

def _coherence_rgb(value):
    v = max(0.0, min(1.0, float(value)))
    hue = (1 - v) * 270.0
    r, g, b = colorsys.hsv_to_rgb((hue % 360) / 360.0, 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))


def _dai_rgb(value):
    v = max(-1.0, min(1.0, float(value)))
    t = (v + 1) / 2

    if t < 0.5:
        c = int(255 * (t / 0.5))
        return (c, c, 255)

    c = int(255 * (1 - (t - 0.5) / 0.5))
    return (255, c, c)

def _aperiodic_rgb(value):
    """
    Maps aperiodic exponent to sequential color.

    Low exponent  -> purple
    High exponent -> red
    """

    if value is None:
        return (200, 200, 200)

    min_val, max_val = METRIC_RANGES["Aperiodic"]

    v = (float(value) - min_val) / (max_val - min_val)
    v = max(0.0, min(1.0, v))

    hue = (1 - v) * 270.0

    r, g, b = colorsys.hsv_to_rgb(
        (hue % 360) / 360.0,
        1.0,
        1.0
    )

    return (
        int(r * 255),
        int(g * 255),
        int(b * 255)
    )


def _difference_rgb(v):
    v = max(-1.0, min(1.0, float(v)))

    if v > 0:
        # white → green
        g = 255
        r = int(255 * (1 - v))
        b = int(255 * (1 - v))
        return (r, g, b)

    else:
        # white → red
        r = 255
        g = int(255 * (1 + v))
        b = int(255 * (1 + v))
        return (r, g, b)


def value_to_rgb(value, metric):

    if value is None:
        return (200, 200, 200)

    if metric in ("Coherence", "PLV"):
        return _coherence_rgb(value)

    if metric == "Aperiodic":
        return _aperiodic_rgb(value)

    if metric == "Difference":
        return _difference_rgb(value)

    return _dai_rgb(value)


def value_to_hex(value, metric):

    r, g, b = value_to_rgb(value, metric)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def difference_to_hex(value, max_difference):
    """
    Maps any signed difference to
    red -> white -> green.
    """

    if max_difference == 0:
        normalized = 0
    else:
        normalized = value / max_difference

    normalized = max(-1.0, min(1.0, normalized))

    r, g, b = _difference_rgb(normalized)

    return "#{:02X}{:02X}{:02X}".format(r, g, b)

