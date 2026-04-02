"""
生成飞书 Agent 桌面图标（.ico）
运行一次即可：python make_icon.py
需要 pillow：pip install pillow
"""
import struct
import os


def create_ico():
    sizes = [256, 64, 32, 16]
    images = []
    for s in sizes:
        png = _make_png(s)
        if png:
            images.append((s, png))

    if not images:
        print("请先安装 Pillow：pip install pillow")
        return

    num_images = len(images)
    header = struct.pack("<HHH", 0, 1, num_images)

    offset = 6 + num_images * 16
    directory = b""
    data = b""

    for size, png_bytes in images:
        w = size if size < 256 else 0
        entry = struct.pack(
            "<BBBBHHII",
            w, w, 0, 0, 1, 32,
            len(png_bytes), offset,
        )
        directory += entry
        data += png_bytes
        offset += len(png_bytes)

    ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feishu_agent.ico")
    with open(ico_path, "wb") as f:
        f.write(header + directory + data)
    print(f"图标已生成: {ico_path}")
    return ico_path


def _make_png(size):
    try:
        import io
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        radius = size // 5
        draw.rounded_rectangle(
            [0, 0, size - 1, size - 1],
            radius=radius,
            fill=(51, 112, 255, 255),
        )

        # 白色文字
        font = None
        for fp in [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
        ]:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, size // 3)
                    break
                except Exception:
                    pass
        if font is None:
            font = ImageFont.load_default()

        text = "飞AI"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            ((size - tw) / 2, (size - th) / 2),
            text, fill=(255, 255, 255, 255), font=font,
        )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        return None


if __name__ == "__main__":
    create_ico()
