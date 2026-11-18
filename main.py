#!/usr/bin/env python3
"""news-image-20261118: draws a front-page montage summing up the world news
of Wednesday 18 November 2026, entirely with the Python standard library.

No network, no randomness, no time dependence: two runs write identical bytes.
Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   ->  out/entry.png
"""
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette ---
PAPER = (247, 243, 232)
INK = (26, 26, 26)
RED = (176, 32, 32)
NAVY = (31, 58, 95)
TEAL = (18, 92, 96)
GOLD = (176, 124, 24)
SLATE = (84, 96, 110)
WHITE = (255, 255, 255)
SKY = (178, 214, 235)
SEA = (64, 128, 170)
SAND = (226, 205, 160)
GREY = (200, 200, 196)
DARKGREY = (120, 120, 116)

# ------------------------------------------------------------- bitmap font --
# 5x7 glyphs, one row per string, "#" = pixel on.  Uppercase only; input is
# upper-cased before drawing.  Written from scratch for this entry.
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "•": ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
}

# ------------------------------------------------------------------ canvas --
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill(bg)

    def fill(self, c):
        r, g, b = c
        self.px[:] = bytes((r, g, b)) * (self.w * self.h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = c
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = bytes((r, g, b)) * (x1 - x0)

    def hline(self, x0, x1, y, c):
        if x0 > x1:
            x0, x1 = x1, x0
        self.rect(x0, y, x1 - x0 + 1, 1, c)

    def vline(self, x, y0, y1, c):
        if y0 > y1:
            y0, y1 = y1, y0
        self.rect(x, y0, 1, y1 - y0 + 1, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, filled=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if filled:
                    if d <= r * r:
                        self.set(xx, yy, c)
                else:
                    if abs(d - r * r) <= r:
                        self.set(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                    self.set(xx, yy, c)

    def triangle(self, p0, p1, p2, c):
        xs = sorted([p0[0], p1[0], p2[0]])
        ys = sorted([p0[1], p1[1], p2[1]])
        for yy in range(ys[0], ys[2] + 1):
            row = []
            for (ax, ay), (bx, by) in ((p0, p1), (p1, p2), (p2, p0)):
                if ay == by:
                    continue
                if min(ay, by) <= yy <= max(ay, by):
                    t = (yy - ay) / (by - ay)
                    row.append(ax + t * (bx - ax))
            if len(row) >= 2:
                self.hline(int(min(row)), int(max(row)), yy, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            row = []
            n = len(pts)
            for i in range(n):
                (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by):
                    t = (yy - ay) / (by - ay)
                    row.append(ax + t * (bx - ax))
            row.sort()
            for i in range(0, len(row) - 1, 2):
                self.hline(int(row[i]), int(row[i + 1]), yy, c)

    def ring(self, cx, cy, r0, r1, c):
        for yy in range(cy - r1, cy + r1 + 1):
            for xx in range(cx - r1, cx + r1 + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if r0 * r0 <= d <= r1 * r1:
                    self.set(xx, yy, c)


# -------------------------------------------------------------- text drawing -
def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color):
    s = s.upper()
    cx = x
    for ch in s:
        g = GLYPHS.get(ch, GLYPHS[" "])
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == "1":
                    cv.rect(cx + gx * scale, y + gy * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def wrap_lines(s, max_chars):
    words = s.upper().split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, s, scale, color, max_w, line_h=None):
    max_chars = max(1, (max_w + scale) // (6 * scale))
    lines = wrap_lines(s, max_chars)
    lh = line_h if line_h is not None else 8 * scale
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * lh, ln, scale, color)
    return y + len(lines) * lh


# --------------------------------------------------------------- PNG output --
def _chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ------------------------------------------------------------------- scenes --
# Each scene draws inside a panel box (x, y, w, h).  Simple flat shapes,
# big and bold so they read at ~300 px wide.

def scene_quad(cv, x, y, w, h):
    # Manila skyline, a plane, and four small flags for the Quad.
    cv.rect(x, y, w, h, SKY)
    cv.circle(x + w - 52, y + 30, 20, (255, 238, 170))
    cv.rect(x, y + h - 46, w, 46, (120, 150, 170))
    # skyline blocks
    heights = [58, 84, 66, 96, 74, 88, 60]
    bx = x + 8
    for hh in heights:
        cv.rect(bx, y + h - 46 - hh, 30, hh, NAVY)
        bx += 40
    # plane
    px, py = x + 60, y + 44
    cv.poly([(px, py), (px + 74, py + 8), (px + 74, py + 14), (px + 16, py + 16)],
            WHITE)
    cv.poly([(px + 30, py + 4), (px + 46, py + 4), (px + 40, py + 14)], WHITE)
    cv.poly([(px + 8, py + 14), (px + 18, py + 14), (px + 12, py + 26)], WHITE)
    # four flags on poles along the bottom
    cols = [(176, 32, 32), (255, 255, 255), (31, 58, 95), (18, 92, 96)]
    for i, c in enumerate(cols):
        fx = x + 24 + i * 74
        cv.vline(fx, y + h - 96, y + h - 46, INK)
        cv.rect(fx, y + h - 96, 34, 22, c)
        cv.rect(fx, y + h - 96, 34, 2, INK)


def scene_bridge(cv, x, y, w, h):
    # The Kerch bridge over the strait, its road arch broken and falling.
    cv.rect(x, y, w, h, (150, 190, 215))
    cv.rect(x, y + h - 52, w, 52, SEA)
    cv.rect(x, y + h - 52, w, 4, (40, 90, 130))
    # bridge deck left and right, gap in the middle
    cv.rect(x, y + 84, 108, 12, INK)
    cv.rect(x + w - 108, y + 84, 108, 12, INK)
    for i in range(4):
        cv.vline(x + 22 + i * 26, y + 96, y + h - 52, INK)
        cv.vline(x + w - 92 + i * 26, y + 96, y + h - 52, INK)
    # standing arch on the left (upper half only, so it reads as an arch)
    import math as _math
    for _r in range(34, 43):
        for _a in range(180, 361):
            _t = _math.radians(_a)
            cv.set(x + 54 + int(_r * _math.cos(_t)),
                   y + 84 + int(_r * _math.sin(_t)), RED)
    # falling span, tilted, into the water
    cv.poly([(x + 178, y + 96), (x + 236, y + 118), (x + 226, y + 132),
             (x + 170, y + 112)], (90, 90, 88))
    cv.poly([(x + 196, y + 118), (x + 236, y + 140), (x + 224, y + 152),
             (x + 188, y + 132)], RED)
    # blast star at the break
    bx, by = x + 168, y + 88
    for dx, dy in ((0, -18), (13, -13), (18, 0), (13, 13), (0, 18),
                   (-13, 13), (-18, 0), (-13, -13)):
        cv.line(bx, by, bx + dx, by + dy, GOLD)
    cv.circle(bx, by, 10, GOLD)
    # smoke puffs
    cv.circle(x + 140, y + 60, 12, (230, 230, 225))
    cv.circle(x + 158, y + 48, 9, (210, 210, 205))
    cv.circle(x + 176, y + 62, 10, (230, 230, 225))
    # wave lines
    for wy in (y + h - 34, y + h - 20):
        for wx in range(x + 10, x + w - 10, 26):
            cv.line(wx, wy, wx + 12, wy, WHITE)
            cv.line(wx + 12, wy, wx + 18, wy - 4, WHITE)


def scene_drones(cv, x, y, w, h):
    # Radar dish, night sky, drones, and an interception burst.
    cv.rect(x, y, w, h, (24, 34, 58))
    for i in range(26):
        sx = x + (i * 37) % w
        sy = y + (i * 29) % (h // 2)
        cv.set(sx, sy, WHITE)
        cv.set(sx + 1, sy, WHITE)
    # radar dish on a base
    dx, dy = x + 70, y + h - 70
    cv.rect(dx - 34, dy, 68, 8, GREY)
    cv.vline(dx, dy - 44, dy, GREY)
    cv.poly([(dx - 52, dy - 78), (dx + 52, dy - 78), (dx, dy - 44)], (200, 200, 196))
    cv.line(dx - 52, dy - 78, dx, dy - 44, WHITE)
    cv.line(dx + 52, dy - 78, dx, dy - 44, WHITE)
    # radar sweep beam
    cv.line(dx, dy - 52, dx + 120, dy - 108, (120, 220, 120))
    cv.line(dx, dy - 52, dx + 128, dy - 96, (120, 220, 120))
    # drones: small quadcopters
    for qx, qy in ((x + 190, y + 46), (x + 246, y + 78), (x + 210, y + 108)):
        cv.rect(qx - 12, qy - 3, 24, 6, INK)
        cv.rect(qx - 18, qy - 6, 10, 3, INK)
        cv.rect(qx + 8, qy - 6, 10, 3, INK)
        cv.circle(qx, qy + 8, 3, RED)
    # interception burst
    bx, by = x + 250, y + 52
    for ddx, ddy in ((0, -16), (12, -12), (16, 0), (12, 12), (0, 16),
                     (-12, 12), (-16, 0), (-12, -12)):
        cv.line(bx, by, bx + ddx, by + ddy, GOLD)
    cv.circle(bx, by, 7, GOLD)
    # ground line
    cv.rect(x, y + h - 12, w, 12, (40, 52, 70))


def scene_sanctions(cv, x, y, w, h):
    # A document stamped SANCTIONED, with building blocks behind it.
    cv.rect(x, y, w, h, (232, 226, 210))
    # buildings
    cv.rect(x + 16, y + 40, 52, h - 40, (150, 158, 168))
    cv.rect(x + 76, y + 22, 52, h - 22, (120, 130, 142))
    cv.rect(x + w - 68, y + 52, 52, h - 52, (150, 158, 168))
    for bx, by in ((x + 28, y + 56), (x + 44, y + 80), (x + 88, y + 38),
                   (x + 104, y + 62), (x + w - 56, y + 68)):
        cv.rect(bx, by, 10, 12, (240, 240, 235))
    # document
    dx, dy = x + w // 2 - 74, y + 34
    cv.rect(dx - 4, dy - 4, 156, 128, INK)
    cv.rect(dx, dy, 148, 120, WHITE)
    for i in range(5):
        cv.rect(dx + 14, dy + 16 + i * 16, 120 - i * 14, 5, INK)
    # red stamp
    cv.rect(dx + 18, dy + 88, 112, 24, RED)
    draw_text(cv, dx + 24, dy + 93, "FROZEN", 2, WHITE)


def scene_trade(cv, x, y, w, h):
    # Cargo ship with containers, two flags, and a rising arrow.
    cv.rect(x, y, w, h, SKY)
    cv.circle(x + w - 48, y + 28, 18, (255, 238, 170))
    cv.rect(x, y + h - 58, w, 58, SEA)
    # ship hull
    cv.poly([(x + 30, y + h - 88), (x + w - 30, y + h - 88),
             (x + w - 62, y + h - 58), (x + 62, y + h - 58)], (40, 44, 52))
    # containers
    cont = [(RED, 0), (NAVY, 1), (GOLD, 2), (TEAL, 3), (RED, 4), (NAVY, 5)]
    for c, i in cont:
        cv.rect(x + 52 + i * 36, y + h - 124, 32, 34, c)
        cv.rect(x + 52 + i * 36, y + h - 124, 32, 2, WHITE)
    # bridge tower
    cv.rect(x + w - 96, y + h - 158, 30, 70, WHITE)
    cv.rect(x + w - 96, y + h - 158, 30, 6, RED)
    # flags: maple leaf mark and stars mark
    cv.vline(x + 52, y + 26, y + 66, INK)
    cv.rect(x + 52, y + 26, 40, 24, RED)
    cv.rect(x + 62, y + 26, 20, 24, WHITE)
    cv.circle(x + 72, y + 38, 6, RED)
    cv.vline(x + w - 92, y + 26, y + 66, INK)
    cv.rect(x + w - 92, y + 26, 40, 24, RED)
    for sx, sy in ((x + w - 84, y + 32), (x + w - 66, y + 32),
                   (x + w - 84, y + 44), (x + w - 66, y + 44),
                   (x + w - 75, y + 38)):
        cv.circle(sx, sy, 2, GOLD)
    # rising arrow in the open sky, centre top
    cv.line(x + 148, y + 56, x + 188, y + 22, (18, 92, 96))
    cv.line(x + 188, y + 22, x + 172, y + 24, (18, 92, 96))
    cv.line(x + 188, y + 22, x + 186, y + 38, (18, 92, 96))


def scene_cyclone(cv, x, y, w, h):
    # Spiral storm over the sea, rain, and a coastline.
    cv.rect(x, y, w, h, (190, 205, 220))
    cx, cy = x + w // 2, y + h // 2 - 12
    # spiral bands
    for r in range(78, 8, -14):
        cv.ring(cx, cy, r - 6, r, WHITE)
    cv.circle(cx, cy, 12, NAVY)
    cv.circle(cx, cy, 5, WHITE)
    # rain streaks
    for i in range(10):
        rx = x + 14 + i * 30
        ry = y + 12 + (i % 3) * 18
        cv.line(rx, ry, rx - 6, ry + 14, (120, 150, 180))
    # coastline and land
    cv.poly([(x, y + h), (x, y + h - 34), (x + 90, y + h - 52),
             (x + 190, y + h - 40), (x + w, y + h - 58), (x + w, y + h)],
            SAND)
    cv.rect(x, y + h - 52, 60, 10, (90, 140, 90))
    # waves
    for wy in (y + h - 22, y + h - 10):
        for wx in range(x + 8, x + w - 8, 24):
            cv.line(wx, wy, wx + 10, wy, WHITE)


# ------------------------------------------------------------------ panels ---
PANELS = [
    dict(kicker="ASIA  •  DIPLOMACY", accent=NAVY, scene=scene_quad,
         head="TRUMP LANDS IN MANILA",
         sub="Quad summit opens Asia trip; APEC in Shenzhen next"),
    dict(kicker="EUROPE  •  WAR", accent=RED, scene=scene_bridge,
         head="CRIMEA BRIDGE HIT",
         sub="Road arch falls; Russia hits two Kyiv bridges"),
    dict(kicker="MIDDLE EAST", accent=TEAL, scene=scene_drones,
         head="DRONES OVER BAHRAIN",
         sub="Iran claims US radar hit; US says all intercepted"),
    dict(kicker="EUROPE  •  UK", accent=GOLD, scene=scene_sanctions,
         head="UK SANCTIONS SETTLERS",
         sub="8 firms frozen over West Bank building"),
    dict(kicker="TRADE  •  APEC", accent=NAVY, scene=scene_trade,
         head="CANADA-CHINA DEAL",
         sub="C$400m tariff relief agreed before APEC opens"),
    dict(kicker="WEATHER  •  INDIA", accent=TEAL, scene=scene_cyclone,
         head="CYCLONE AKVAN NEARS",
         sub="Storm strengthens over Bay of Bengal; coasts on alert"),
]


def draw_panel(cv, px, py, pw, ph, p):
    cv.rect(px, py, pw, ph, WHITE)
    cv.rect(px, py, pw, 2, p["accent"])
    cv.rect(px, py + ph - 2, pw, 2, p["accent"])
    cv.rect(px, py, 2, ph, p["accent"])
    cv.rect(px + pw - 2, py, 2, ph, p["accent"])
    # kicker strip
    cv.rect(px + 2, py + 2, pw - 4, 30, p["accent"])
    draw_text(cv, px + 12, py + 10, p["kicker"], 2, WHITE)
    # scene
    sx, sy, sw, sh = px + 10, py + 42, pw - 20, 196
    p["scene"](cv, sx, sy, sw, sh)
    cv.rect(sx, sy, sw, 2, INK)
    cv.rect(sx, sy + sh - 2, sw, 2, INK)
    # headline + sub
    hy = py + 42 + 196 + 14
    draw_block(cv, px + 12, hy, p["head"], 3, INK, pw - 24)
    draw_block(cv, px + 12, hy + 56, p["sub"], 2, SLATE, pw - 24)


# --------------------------------------------------------------------- page --
def build():
    cv = Canvas(W, H, PAPER)
    # masthead
    draw_text(cv, (W - text_width("THE WORLD IN ONE DAY", 2)) // 2, 14,
              "THE WORLD IN ONE DAY", 2, RED)
    cv.hline(16, W - 16, 44, INK)
    cv.hline(16, W - 16, 48, INK)
    title = "WEDNESDAY 18 NOVEMBER 2026"
    draw_text(cv, (W - text_width(title, 5)) // 2, 60, title, 5, INK)
    cv.hline(16, W - 16, 108, INK)
    cv.hline(16, W - 16, 112, RED)
    # grid: 3 x 2 panels
    pw, ph = 320, 400
    for i, p in enumerate(PANELS):
        px = 16 + (i % 3) * (pw + 16)
        py = 126 + (i // 3) * (ph + 12)
        draw_panel(cv, px, py, pw, ph, p)
    # footer strip
    fy = 126 + 2 * ph + 12 + 10
    cv.rect(16, fy, W - 32, 40, NAVY)
    draw_text(cv, 28, fy + 12, "ALSO: DHONI ENDS IPL CAREER, NAMED CSK MENTOR",
              2, WHITE)
    draw_text(cv, 28, fy + 52, "ALL STORIES AS REPORTED ON 18 NOVEMBER 2026",
              1, SLATE)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))
    return 0


if __name__ == "__main__":
    sys.exit(main())
