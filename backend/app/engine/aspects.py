"""Aspects between chart bodies. Orb is measured on each side of the exact angle."""
from __future__ import annotations

from .models import Aspect, AspectSettings, BodyPosition

MAJOR = {"conjunction": 0.0, "sextile": 60.0, "square": 90.0, "trine": 120.0, "opposition": 180.0}
MINOR = {"semisextile": 30.0, "semisquare": 45.0, "sesquiquadrate": 135.0, "quincunx": 150.0}
LUMINARIES = {"sun", "moon"}
DEFAULT_EXCLUDE = {"fortune"}


def _separation(x: float, y: float) -> float:
    return abs((x - y + 180) % 360 - 180)


def find_aspects(bodies: dict[str, BodyPosition], settings: AspectSettings, exclude: set[str] | None = None) -> list[Aspect]:
    exclude = DEFAULT_EXCLUDE if exclude is None else exclude
    table = dict(MAJOR)
    if settings.minor_aspects:
        table.update(MINOR)
    keys = [k for k in bodies if k not in exclude]
    out: list[Aspect] = []
    for i, ka in enumerate(keys):
        for kb in keys[i + 1:]:
            pa, pb = bodies[ka], bodies[kb]
            sep = _separation(pa.lon, pb.lon)
            bonus = settings.luminary_bonus if (ka in LUMINARIES or kb in LUMINARIES) else 0.0
            best: Aspect | None = None
            for name, angle in table.items():
                max_orb = (settings.orbs.get(name, settings.minor_orb) if name in MAJOR else settings.minor_orb) + bonus
                orb = abs(sep - angle)
                if orb <= max_orb and (best is None or orb < best.orb):
                    # applying: separation moving toward the exact angle over the next instant
                    future = _separation(pa.lon + pa.speed_lon / 1440, pb.lon + pb.speed_lon / 1440)
                    best = Aspect(a=ka, b=kb, type=name, angle=angle, separation=sep, orb=orb, max_orb=max_orb,
                                  applying=abs(future - angle) < orb, exact=orb < 1e-9)
            if best is not None:
                out.append(best)
    out.sort(key=lambda x: x.orb)
    return out
