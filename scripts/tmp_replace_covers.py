#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
替换 Astro-blog 封面类图片：
- 从 D:\\Temp\\wallpapers\\selected 中按宽高比(AR)贪心匹配候选图
- center-crop 到目标封面分辨率，转 WEBP
- 原封面备份到 Astro-blog/temp_cover_backup/
"""
import os, sys, shutil, json
from PIL import Image

BLOG_DIR = r'E:\Documents\Projects\Astro-blog'
SELECTED = r'D:\Temp\wallpapers\selected'
COVER_DIR = os.path.join(BLOG_DIR, 'public', 'img', 'cover')
BACKUP_DIR = os.path.join(BLOG_DIR, 'temp_cover_backup')

# 目标封面: (路径, 目标分辨率)
targets = []
for i in range(1, 22):
    p = os.path.join(COVER_DIR, f'{i}.webp')
    if os.path.exists(p):
        with Image.open(p) as im:
            targets.append((p, im.size))
weekly = os.path.join(BLOG_DIR, 'public', 'img', 'weekly_header.webp')
if os.path.exists(weekly):
    with Image.open(weekly) as im:
        targets.append((weekly, im.size))

# 候选图: (路径, 尺寸, AR)
candidates = []
for f in sorted(os.listdir(SELECTED)):
    p = os.path.join(SELECTED, f)
    if not os.path.isfile(p):
        continue
    if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')):
        continue
    try:
        with Image.open(p) as im:
            w, h = im.size
            candidates.append((p, (w, h), w / h))
    except Exception as e:
        print(f'跳过 {f}: {e}')

print(f'目标封面: {len(targets)} 张, 候选图: {len(candidates)} 张')
used = set()

def pick(ar):
    """贪心: 找 AR 最接近且未使用的候选"""
    best, best_diff = None, 1e9
    for idx, (p, size, car) in enumerate(candidates):
        if idx in used:
            continue
        diff = abs(car - ar)
        if diff < best_diff:
            best, best_diff = idx, diff
    return best

os.makedirs(BACKUP_DIR, exist_ok=True)
manifest = []

for tpath, (tw, th) in targets:
    tar = tw / th
    idx = pick(tar)
    if idx is None:
        print(f'!! 无可用候选: {tpath}')
        continue
    cp, (cw, ch), car = candidates[idx]
    used.add(idx)

    # 备份原文件
    rel = os.path.relpath(tpath, BLOG_DIR)
    bak = os.path.join(BACKUP_DIR, rel.replace(os.sep, '__'))
    os.makedirs(os.path.dirname(bak), exist_ok=True)
    shutil.copy2(tpath, bak)

    # center-crop 到目标 AR
    with Image.open(cp) as im:
        im = im.convert('RGB')
        imw, imh = im.size
        target_ar = tw / th
        cur_ar = imw / imh
        if cur_ar > target_ar:
            # 太宽: 裁剪宽度
            new_w = int(imh * target_ar)
            x0 = (imw - new_w) // 2
            im = im.crop((x0, 0, x0 + new_w, imh))
        else:
            # 太高: 裁剪高度
            new_h = int(imw / target_ar)
            y0 = (imh - new_h) // 2
            im = im.crop((0, y0, imw, y0 + new_h))
        # resize 到目标分辨率
        im = im.resize((tw, th), Image.LANCZOS)
        im.save(tpath, 'WEBP', quality=82, method=6)

    manifest.append({
        'target': rel,
        'target_size': f'{tw}x{th}',
        'source': os.path.basename(cp),
        'source_size': f'{cw}x{ch}',
        'backup': os.path.relpath(bak, BLOG_DIR),
    })
    print(f'✓ {rel} ({tw}x{th}) ← {os.path.basename(cp)} ({cw}x{ch})')

with open(os.path.join(BLOG_DIR, 'temp_cover_backup', 'replace_manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print(f'\n完成: 替换 {len(manifest)} 张, 备份到 {BACKUP_DIR}')
