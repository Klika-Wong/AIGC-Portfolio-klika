#!/usr/bin/env python3
"""Make a *more narrowly isolated* bangs candidate using the ORIGINAL image pixels.
No regeneration, no facial redesign; residual mask still needs an artist to paint/fill.
"""
import argparse, json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

# Hand-audited approximate root/front-fringe boundary for the 1024x1536 original.
FRONT_HAIR_OUTLINE = [
 (444,40),(467,32),(495,33),(520,40),(546,62),(562,90),
 (568,112),(578,146),(565,163),(547,158),(528,147),
 (513,150),(503,146),(491,153),(483,153),(476,155),
 (465,167),(455,171),(440,173),(430,173),(417,171),
 (408,162),(399,149),(398,127),(406,94),(420,64)
]

def run(source: Path, assets: Path):
    rgb=np.asarray(Image.open(source).convert("RGB"))
    height,width=rgb.shape[:2]
    if (width,height)!=(1024,1536):raise ValueError("Reference geometry changed; re-annotate fringe manually")
    old=assets/"00_subject_cutout_refined.png"
    if not old.is_file():old=assets/"00_subject_cutout.png"
    fullalpha=np.asarray(Image.open(old).convert("RGBA"))[:,:,3]
    outline=np.zeros((height,width),np.uint8)
    cv2.fillPoly(outline,[np.asarray(FRONT_HAIR_OUTLINE,dtype=np.int32)],255)
    luminance=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB)[:,:,0]
    red_minus_blue=rgb[:,:,0].astype(np.int16)-rgb[:,:,2].astype(np.int16)
    skinlike=red_minus_blue>16
    rough=((luminance<137)&(~skinlike)&(outline>0)&(fullalpha>0)).astype(np.uint8)
    rough=cv2.morphologyEx(rough,cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
    n,ids,stats,_=cv2.connectedComponentsWithStats(rough,8)
    if n<2:raise ValueError("No usable fringe pixels")
    keep=int(np.argmax(stats[1:,cv2.CC_STAT_AREA])+1)
    alpha=np.where(ids==keep,255,0).astype(np.uint8)
    alpha=cv2.GaussianBlur(alpha,(3,3),.4)
    alpha=np.minimum(alpha,fullalpha)
    rgba=np.dstack([rgb,alpha]);rgba[alpha==0,:3]=0
    Image.fromarray(rgba,"RGBA").save(assets/"05_front_hair_isolation_candidate.png",compress_level=3)
    result={
      "name":"front_hair_isolation_candidate",
      "label":"较精细刘海候选（未补画）",
      "file":"05_front_hair_isolation_candidate.png",
      "bbox":list(Image.fromarray(rgba,"RGBA").getbbox() or [0,0,0,0]),
      "source_pixels_repainted":0,
      "rig_ready":False,
      "warning":"Hair boundary is approximate; glossy holes, root/ear overlap, missing forehead below the fringe still require manual repainting."
    }
    (assets/"05_front_hair_notes.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Refined front-hair candidate:",int(np.sum(alpha>128)),"opaque px; still not rig-ready")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",required=True,type=Path);p.add_argument("--assets",required=True,type=Path)
    a=p.parse_args();run(a.source,a.assets)
