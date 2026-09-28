#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/generate_app_icon.py - 生成「玄鉴·书房」macOS 官方高规格 AppIcon.icns
"""

import os
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont

def generate_base_icon(output_png_1024: str):
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. 绘制带有圆角与微质感底蕴的宣纸色背景底板 (Squircle)
    margin = 48
    bg_box = [margin, margin, size - margin, size - margin]
    corner_radius = 210

    # 宣纸底色 #F7F4EC
    draw.rounded_rectangle(bg_box, radius=corner_radius, fill=(247, 244, 236, 255), outline=(43, 51, 62, 50), width=6)

    # 2. 内部宋式黛青内框
    inner_margin = margin + 36
    draw.rounded_rectangle(
        [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
        radius=corner_radius - 24,
        outline=(33, 56, 68, 80),
        width=3
    )

    # 3. 中心朱砂八卦阳爻/阴爻与印章徽标
    center_x = size // 2
    center_y = size // 2

    # 朱砂印章外框 #C3272B
    seal_size = 460
    seal_box = [
        center_x - seal_size // 2,
        center_y - seal_size // 2,
        center_x + seal_size // 2,
        center_y + seal_size // 2
    ]
    draw.rounded_rectangle(seal_box, radius=64, fill=(195, 39, 43, 245), outline=(150, 25, 30, 255), width=8)

    # 印章内部阴刻装饰框
    seal_inner = [b + 24 if i < 2 else b - 24 for i, b in enumerate(seal_box)]
    draw.rounded_rectangle(seal_inner, radius=48, outline=(247, 244, 236, 180), width=4)

    # 印面文字绘制
    # 尝试加载中文字体，若无则绘制古典卦符图案
    font_loaded = False
    for font_path in [
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf"
    ]:
        if os.path.exists(font_path):
            try:
                font_large = ImageFont.truetype(font_path, 150)
                font_sub = ImageFont.truetype(font_path, 60)
                # 绘制“玄鉴”
                draw.text((center_x, center_y - 45), "玄鉴", fill=(247, 244, 236, 255), font=font_large, anchor="mm")
                # 绘制“书房”
                draw.text((center_x, center_y + 110), "书 房", fill=(247, 244, 236, 230), font=font_sub, anchor="mm")
                font_loaded = True
                break
            except Exception:
                continue

    if not font_loaded:
        # 回退绘制象征性乾卦三阳爻金文图形
        bar_w = 260
        bar_h = 32
        for offset_y in [-90, 0, 90]:
            draw.rectangle(
                [center_x - bar_w // 2, center_y + offset_y - bar_h // 2, center_x + bar_w // 2, center_y + offset_y + bar_h // 2],
                fill=(247, 244, 236, 255)
            )

    # 4. 印章上方小字题记
    for font_path in ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Light.ttc"]:
        if os.path.exists(font_path):
            try:
                tag_font = ImageFont.truetype(font_path, 34)
                draw.text((center_x, margin + 70), "慎 初 · 守 正", fill=(43, 51, 62, 190), font=tag_font, anchor="mm")
                draw.text((center_x, size - margin - 70), "象 数 求 真 · 依 实 而 动", fill=(43, 51, 62, 190), font=tag_font, anchor="mm")
                break
            except Exception:
                pass

    img.save(output_png_1024, "PNG")
    print(f"基础 1024x1024 图标已生成: {output_png_1024}")


def make_icns(source_png_1024: str, target_icns_path: str):
    with tempfile.TemporaryDirectory() as td:
        iconset_dir = os.path.join(td, "AppIcon.iconset")
        os.makedirs(iconset_dir, exist_ok=True)

        sizes = [
            (16, "icon_16x16.png"),
            (32, "icon_16x16@2x.png"),
            (32, "icon_32x32.png"),
            (64, "icon_32x32@2x.png"),
            (128, "icon_128x128.png"),
            (256, "icon_128x128@2x.png"),
            (256, "icon_256x256.png"),
            (512, "icon_256x256@2x.png"),
            (512, "icon_512x512.png"),
            (1024, "icon_512x512@2x.png")
        ]

        src_img = Image.open(source_png_1024)
        for sz, filename in sizes:
            resized = src_img.resize((sz, sz), Image.Resampling.LANCZOS)
            resized.save(os.path.join(iconset_dir, filename))

        os.makedirs(os.path.dirname(os.path.abspath(target_icns_path)), exist_ok=True)
        cmd = ["iconutil", "-c", "icns", iconset_dir, "-o", target_icns_path]
        subprocess.check_call(cmd)
        print(f"macOS 官方 ICNS 已构建成功: {target_icns_path}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build_assets")
    os.makedirs(out_dir, exist_ok=True)
    base_png = os.path.join(out_dir, "app_icon_1024.png")
    out_icns = os.path.join(out_dir, "AppIcon.icns")
    generate_base_icon(base_png)
    make_icns(base_png, out_icns)
