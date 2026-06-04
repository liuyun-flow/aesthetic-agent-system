#!/usr/bin/env python3
"""PDF 背景变白 — 将扫描版 PDF 的背景替换为纯白色。

用法:
    python3 whiten_pdf.py <input.pdf> [output.pdf] [--level normal|high|low]

等级:
    normal - 默认，平衡的白化效果
    high   - 更激进，灰底清除更彻底（适合打印要求高的场景）
    low    - 保守，更多地保留过渡色（适合有大量彩色内容的 PDF）

改进:
    - 分块背景估计：将图片分成网格，独立采样每块的背景色
    - 空间自适应白化：根据像素位置使用局部背景色
    - 异常块检测与修复：替换被内容填充的异常采样块
    - 质量检查：输出每页的背景均匀度和纯白率
"""

import sys, os, argparse
from PIL import Image
import io
import numpy as np

try:
    import pymupdf
except ImportError:
    print("错误：需要安装 pymupdf。运行: python3 -m pip install pymupdf Pillow numpy")
    sys.exit(1)


def build_background_map(img_np, grid_cols, grid_rows):
    """分块估计背景色，返回插值函数。"""
    h, w = img_np.shape[:2]
    bw = w // grid_cols
    bh = h // grid_rows

    bg_map = np.zeros((grid_rows, grid_cols, 3), dtype=np.float32)

    for gy in range(grid_rows):
        for gx in range(grid_cols):
            x0, y0 = gx * bw, gy * bh
            x1 = min(x0 + bw, w)
            y1 = min(y0 + bh, h)
            strip = 8

            samples = []
            # Top strip
            for y in range(y0, min(y0 + strip, y1)):
                for x in range(x0 + strip, x1 - strip):
                    if 0 <= y < h and 0 <= x < w:
                        samples.append(img_np[y, x])
            # Bottom strip
            for y in range(max(y1 - strip, y0 + strip), y1):
                for x in range(x0 + strip, x1 - strip):
                    if 0 <= y < h and 0 <= x < w:
                        samples.append(img_np[y, x])
            # Left strip
            for y in range(y0 + strip, y1 - strip):
                for x in range(x0, min(x0 + strip, x1)):
                    if 0 <= y < h and 0 <= x < w:
                        samples.append(img_np[y, x])
            # Right strip
            for y in range(y0 + strip, y1 - strip):
                for x in range(max(x1 - strip, x0 + strip), x1):
                    if 0 <= y < h and 0 <= x < w:
                        samples.append(img_np[y, x])

            if samples:
                samples = np.array(samples)
                bg_map[gy, gx] = np.median(samples, axis=0)
            else:
                bg_map[gy, gx] = [200, 200, 200]

    # 异常块检测：亮度偏离邻居中位数过多的块，用邻居均值替换
    for gy in range(grid_rows):
        for gx in range(grid_cols):
            neighbors = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = gy + dy, gx + dx
                    if 0 <= ny < grid_rows and 0 <= nx < grid_cols:
                        neighbors.append(bg_map[ny, nx])

            if neighbors:
                neighbors = np.array(neighbors)
                self_bright = bg_map[gy, gx].sum()
                neighbor_brights = neighbors.sum(axis=1)
                median_bright = np.median(neighbor_brights)

                if abs(self_bright - median_bright) > 60:
                    bg_map[gy, gx] = neighbors.mean(axis=0)

    def get_local_bg(x, y):
        """双线性插值获取 (x,y) 处的局部背景色。"""
        gx = np.clip((x / w) * (grid_cols - 1), 0, grid_cols - 1.001)
        gy = np.clip((y / h) * (grid_rows - 1), 0, grid_rows - 1.001)
        ix, iy = int(gx), int(gy)
        fx, fy = gx - ix, gy - iy
        ix2 = min(ix + 1, grid_cols - 1)
        iy2 = min(iy + 1, grid_rows - 1)

        result = np.zeros(3, dtype=np.float32)
        for c in range(3):
            v00 = bg_map[iy, ix, c]
            v10 = bg_map[iy, ix2, c]
            v01 = bg_map[iy2, ix, c]
            v11 = bg_map[iy2, ix2, c]
            result[c] = (1-fy)*((1-fx)*v00 + fx*v10) + fy*((1-fx)*v01 + fx*v11)
        return result

    return get_local_bg, bg_map


def whiten_image(img_np, level="normal"):
    """对单张图片进行背景白化处理。返回 (result, quality_report)。"""
    h, w = img_np.shape[:2]

    cfg = {
        "low":    {"power": 0.6,  "final_power": 0.7,  "min_thresh": 150},
        "normal": {"power": 0.35, "final_power": 0.5,  "min_thresh": 130},
        "high":   {"power": 0.25, "final_power": 0.35, "min_thresh": 110},
    }[level]

    # 分块背景估计
    grid_cols = max(4, w // 150)
    grid_rows = max(4, h // 150)
    get_local_bg, bg_map = build_background_map(img_np, grid_cols, grid_rows)

    # 步骤 1：局部背景白化
    result = np.zeros_like(img_np)
    bg_std = np.array([14, 13, 12])
    low = np.maximum(bg_std * 1.2, 15)
    high = np.maximum(bg_std * 5, 80)

    # 向量化处理：为每个像素计算局部背景
    ys, xs = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    local_bg = np.zeros((h, w, 3), dtype=np.float32)

    # 使用双线性插值批量计算
    gx = np.clip((xs / w) * (grid_cols - 1), 0, grid_cols - 1.001)
    gy = np.clip((ys / h) * (grid_rows - 1), 0, grid_rows - 1.001)
    ix = gx.astype(int)
    iy = gy.astype(int)
    fx = gx - ix
    fy = gy - iy
    ix2 = np.minimum(ix + 1, grid_cols - 1)
    iy2 = np.minimum(iy + 1, grid_rows - 1)

    for c in range(3):
        v00 = bg_map[iy, ix, c]
        v10 = bg_map[iy, ix2, c]
        v01 = bg_map[iy2, ix, c]
        v11 = bg_map[iy2, ix2, c]
        local_bg[:, :, c] = (1-fy)*((1-fx)*v00 + fx*v10) + fy*((1-fx)*v01 + fx*v11)

    for c in range(3):
        diff_c = np.abs(img_np[:, :, c] - local_bg[:, :, c])
        mask_c = np.clip((diff_c - low[c]) / (high[c] - low[c]), 0.0, 1.0)
        result[:, :, c] = mask_c * img_np[:, :, c] + (1.0 - mask_c) * 255.0

    # 步骤 2：强力清除灰底
    min_ch = result.min(axis=2)
    light = min_ch > cfg["min_thresh"]
    if light.sum() > 0:
        lm = min_ch[light].astype(np.float32)
        blend_raw = np.clip((lm - cfg["min_thresh"]) / 100.0, 0.0, 1.0)
        blend = blend_raw ** cfg["power"]
        blend_3d = np.stack([blend, blend, blend], axis=1)
        result[light] = (1.0 - blend_3d) * result[light] + blend_3d * 255.0

    # 步骤 3：最终扫尾
    min_ch2 = result.min(axis=2)
    max_ch2 = result.max(axis=2)
    still_gray = (min_ch2 > 180) & (max_ch2 < 248)
    if still_gray.sum() > 0:
        final_blend = np.clip((min_ch2[still_gray] - 180) / 50.0, 0.0, 1.0) ** cfg["final_power"]
        fb_3d = np.stack([final_blend, final_blend, final_blend], axis=1)
        result[still_gray] = (1.0 - fb_3d) * result[still_gray] + fb_3d * 255.0

    result = np.clip(result, 0, 255)

    # 质量检查
    q = check_quality(result)
    return result, q


def check_quality(img_np):
    """检查处理后图片的背景均匀度。"""
    h, w = img_np.shape[:2]
    margin = 20
    strip = 15

    samples = []
    # Top edge
    for y in range(5, strip):
        for x in range(margin, w - margin, 4):
            samples.append(img_np[y, x])
    # Bottom edge
    for y in range(h - strip, h - 5):
        for x in range(margin, w - margin, 4):
            samples.append(img_np[y, x])

    if not samples:
        return {"grade": "unknown", "white_pct": 0, "std_dev": 0, "message": "无法检测"}

    samples = np.array(samples, dtype=np.float32)
    std_dev = float(samples.std())

    white_count = int(np.all(samples > 245, axis=1).sum())
    white_pct = white_count / len(samples)

    if white_pct > 0.95 and std_dev < 8:
        grade = "good"
        message = f"背景均匀 ({white_pct*100:.0f}% 纯白)"
    elif white_pct > 0.80 and std_dev < 20:
        grade = "ok"
        message = f"背景基本均匀 ({white_pct*100:.0f}% 纯白)，建议用强力模式重试"
    else:
        grade = "bad"
        message = f"背景不够均匀 ({white_pct*100:.0f}% 纯白)，建议用强力模式重试"

    return {"grade": grade, "white_pct": white_pct, "std_dev": round(std_dev, 1), "message": message}


def whiten_pdf(input_path, output_path, level="normal"):
    """将 PDF 背景变为白色。返回质量报告列表。"""

    doc = pymupdf.open(input_path)
    page_count = doc.page_count
    quality_reports = []

    for page_num in range(page_count):
        page = doc[page_num]
        images = page.get_images(full=True)

        if not images:
            print(f"  第 {page_num+1} 页：无图片，跳过")
            quality_reports.append({"grade": "skip", "white_pct": 0, "std_dev": 0, "message": "无图片"})
            continue

        xref = images[0][0]
        base_image = doc.extract_image(xref)

        img = Image.open(io.BytesIO(base_image["image"]))
        img_np = np.array(img).astype(np.float32)

        # 处理
        result_np, q = whiten_image(img_np, level)
        quality_reports.append(q)

        print(f"  第 {page_num+1} 页: {q['message']} (std={q['std_dev']})")

        # 替换图片
        result_img = Image.fromarray(result_np.astype(np.uint8), mode='RGB')
        img_bytes = io.BytesIO()
        result_img.save(img_bytes, format='JPEG', quality=92)
        img_bytes.seek(0)
        page.replace_image(xref, stream=img_bytes.read())

    doc.save(output_path, deflate=True, garbage=3)
    doc.close()

    return quality_reports


def main():
    parser = argparse.ArgumentParser(description="将扫描版 PDF 的背景色替换为纯白色")
    parser.add_argument("input", help="输入 PDF 文件路径")
    parser.add_argument("output", nargs="?", default=None, help="输出 PDF 文件路径（默认：在输入文件名后加 _白底）")
    parser.add_argument("--level", "-l", choices=["low", "normal", "high"], default="normal",
                        help="激进程度：low=保守, normal=默认, high=最激进（默认: normal）")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误：找不到文件 {args.input}")
        sys.exit(1)

    if args.output is None:
        base, ext = os.path.splitext(args.input)
        args.output = f"{base}_白底{ext}"

    print(f"输入: {args.input}")
    print(f"输出: {args.output}")
    print(f"等级: {args.level}")
    print(f"处理中...")

    reports = whiten_pdf(args.input, args.output, args.level)

    in_size = os.path.getsize(args.input) / 1024
    out_size = os.path.getsize(args.output) / 1024

    # 汇总质量
    grades = [r["grade"] for r in reports if r["grade"] != "skip"]
    if grades:
        good_count = grades.count("good")
        ok_count = grades.count("ok")
        bad_count = grades.count("bad")
        print(f"\n质量汇总: 🟢{good_count} 🟡{ok_count} 🔴{bad_count}")
        if bad_count > 0:
            print("建议: 用 --level high 重试以获得更好效果")

    print(f"完成！原文件: {in_size:.0f} KB → 新文件: {out_size:.0f} KB")


if __name__ == "__main__":
    main()
