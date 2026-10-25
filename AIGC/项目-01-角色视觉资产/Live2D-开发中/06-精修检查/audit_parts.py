#!/usr/bin/env python3
"""Non-generative original-avatar detail audit. Only tiny alpha pinholes are repaired.
Does NOT split independently drawable eyes/mouth/hair or produce a Cubism model.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import cv2
import numpy as np

def png_subject(original: Image.Image, rgba: np.ndarray, out: Path):
    # Preserve exact original RGB values; only changing some alpha pixels on the scalp.
    arr = np.asarray(original.convert("RGB"))
    rgba = rgba.copy()
    fg = rgba[:,:,3] > 0
    rgba[fg,:3] = arr[fg]
    rgba[~fg,:3] = 0
    Image.fromarray(rgba,"RGBA").save(out,compress_level=4)

def audit(source_path: Path, asset_dir: Path) -> dict:
    src = Image.open(source_path).convert("RGB")
    fg = Image.open(asset_dir/"00_subject_cutout.png").convert("RGBA")
    if src.size != fg.size:
        raise ValueError("Source and foreground pixel dimensions differ")
    w,h = src.size
    if (w,h) != (1024,1536):
        raise ValueError("This source-specific audit is only calibrated for the 1024 x 1536 original")

    manifest = json.loads((asset_dir/"manifest.json").read_text(encoding="utf-8"))
    records = manifest.get("parts") or manifest.get("layers") or []
    arr = np.asarray(fg).copy()
    before = arr[:,:,3].copy()
    a = before.copy()

    # Fill only small enclosed micro-holes within the dark central scalp.
    # Do not close wide hair gaps; those may be intentional background openings.
    x1,y1,x2,y2 = 390,40,590,145
    roi=(a[y1:y2,x1:x2] > 128).astype("uint8")
    count,components,stats,_=cv2.connectedComponentsWithStats(1-roi,8)
    holes=[]
    for label in range(1,count):
        x,y,cw,ch,size = [int(v) for v in stats[label]]
        enclosed = x>0 and y>0 and x+cw<roi.shape[1] and y+ch<roi.shape[0]
        if enclosed and 1<=size<=45:
            # Restore source-color sample at previously transparent pixels.
            patch = a[y1:y2,x1:x2]
            patch[components==label]=255
            holes.append({"x":x+x1,"y":y+y1,"pixels":size})
    arr[:,:,3]=a
    png_subject(src,arr,asset_dir/"00_subject_cutout_refined.png")

    # Quantify pixel fidelity. Colours in opaque candidate regions should be original.
    source_rgb=np.asarray(src)
    fidelity={}
    occupancy=np.zeros((h,w),dtype=np.uint8)
    for rec in records:
        name=rec.get("name") or rec.get("id")
        rel=rec.get("file") or rec.get("path")
        if not rel or not name:continue
        path=asset_dir/rel
        if not path.is_file():raise FileNotFoundError(f"missing transparent layer: {rel}")
        im=np.asarray(Image.open(path).convert("RGBA"))
        if im.shape[:2]!=(h,w):raise AssertionError(f"pixel alignment mismatch: {name}")
        visible=im[:,:,3]>128
        occupancy += visible.astype("uint8")
        # Tiny RGB differences can happen in edge preprocessing; quantify instead of assuming perfect.
        d=np.abs(im[:,:,:3].astype("int16")-source_rgb.astype("int16")).max(axis=2)
        changed=int(np.count_nonzero(visible&(d>2)))
        fidelity[name]={"opaque_pixels":int(visible.sum()),"changed_source_color_pixels":changed,
                        "suitable_for_direct_cubism_rig":False}
    multilayer=int(np.count_nonzero(occupancy>1))
    report={
        "version":"0.4.0","reference":str(source_path.name),
        "source_resolution":[w,h],"candidate_part_count":len(fidelity),
        "identity_reference_color_preserved":all(v["changed_source_color_pixels"]==0 for v in fidelity.values()),
        "overlap_pixel_count":multilayer,
        "scalp_alpha_microhole_pixels_repaired":int(np.count_nonzero(a!=before)),
        "scalp_repaired_holes":holes,
        "model3_status":"NOT_GENERATED",
        "attention_required":[
           "Hair/bangs ROI overlaps skin and clothing; separate hair strands and paint occulted skin manually",
           "Eyes are excerpts, not separately movable iris/eyelid/white parts",
           "Mouth is a source excerpt; missing jaw interior/teeth/tongue and lip keyforms",
           "Current regions overlap each other; not a clean PSD-ready Live2D layer structure",
           "Face close-up resolution from original is small; higher resolution repaint must preserve identity",
           "Boot edges, pendulum, bracelet, pocket items need hand-checked pixel masks"
        ],
        "per_part":fidelity
    }
    (asset_dir/"04_quality_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")

    # One compact visual verification board built only from original pixels and existing masks.
    board=Image.new("RGB",(1280,755),(237,240,237))
    pen=ImageDraw.Draw(board)
    font=ImageFont.load_default()
    pen.text((24,12),"Klika | Original face | Face candidate | Bangs candidate | Eye and mouth sources",fill=(39,53,45),font=font)
    checks=[("Original",None,(365,35,620,305)),
            ("Face ROI","face_base",(365,35,620,305)),
            ("Bangs ROI","hair_bangs",(365,35,620,305)),
            ("Eyes and lips ROI","eye_left_source",(400,134,562,277))]
    byname={r.get("name") or r.get("id"):r for r in records}
    for i,(title,name,crop) in enumerate(checks):
        x=20+i*315
        pen.rounded_rectangle((x,52,x+297,735),radius=16,fill=(251,252,249),outline=(201,209,202),width=2)
        pen.text((x+12,65),title,fill=(42,67,53),font=font)
        if name is None:
            selected=src.convert("RGBA")
        else:
            selected=Image.open(asset_dir/(byname[name].get("file") or byname[name].get("path"))).convert("RGBA")
        if name=="eye_left_source":
            base_part=Image.new("RGBA",src.size,(0,0,0,0))
            for small in ("eye_left_source","eye_right_source","mouth_source","brows_source"):
                r=byname.get(small)
                if r is None:continue
                piece=Image.open(asset_dir/(r.get("file") or r.get("path"))).convert("RGBA")
                base_part.alpha_composite(piece)
            selected=base_part
        roi=selected.crop(crop)
        roi.thumbnail((272,605),Image.Resampling.LANCZOS)
        roi=roi.resize((272,605),Image.Resampling.NEAREST) if roi.size[0]<272 else roi
        chec=Image.new("RGBA",(272,605),(247,249,247,255))
        pd=ImageDraw.Draw(chec)
        for yy in range(0,605,20):
            for xx in range(0,272,20):
                if (xx//20+yy//20)%2==0:pd.rectangle((xx,yy,xx+19,yy+19),fill=(226,231,226,255))
        # preserve aspect ratio
        panel=selected.crop(crop)
        panel.thumbnail((272,605),Image.Resampling.LANCZOS)
        chec.alpha_composite(panel,((272-panel.width)//2,(605-panel.height)//2))
        board.paste(chec.convert("RGB"),(x+12,102))
    board.save(asset_dir/"04_face_detail_audit.png",compress_level=4)
    if len(fidelity)<20:raise AssertionError("Unexpectedly few asset regions; audit interrupted")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--assets",required=True,type=Path)
    a=p.parse_args()
    report=audit(a.source,a.assets)
    print("Original-preserving scalp repairs:",report["scalp_alpha_microhole_pixels_repaired"])
    print("Reference regions audited:",report["candidate_part_count"],"overlap:",report["overlap_pixel_count"])
