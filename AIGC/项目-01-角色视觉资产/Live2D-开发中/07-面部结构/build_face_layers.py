#!/usr/bin/env python3
"""Source-locked Klika facial part extraction: true RGBA layers, NOT a Cubism .moc3.

The first version's rectangular eye/lip crops could not move independently.
This script separates gaze irises and a source-backed neutral eye/mouth stack,
with an editable ORA and an image-reassembly regression test. It does NOT
pretend missing closed eyelid / oral cavity art is finished.
"""
from __future__ import annotations
import argparse, io, json, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np
from PIL import Image, ImageDraw
W,H=1024,1536
# image-left vs image-right, NOT character's anatomical left/right.
PARTS={
 "eye_image_left": ((451,187),(19,12),-7),
 "eye_image_right":((507,174),(23,13),-18),
 "brow_image_left":((447,173),(19,4),-8),
 "brow_image_right":((490,160),(25,5),-25),
 "mouth":((489,229),(25,13),-9),
 "iris_image_left":((452,185),(7,6),-5),
 "iris_image_right":((508,173),(8,7),-12)}
SKIN={
 "eye_image_left":((442,201),(468,199)),
 "eye_image_right":((489,193),(523,195)),
 "brow_image_right":((478,182),(510,185)),
 "mouth":((469,211),(510,212))}
def stencil(name):
    center,radii,angle=PARTS[name]
    alpha=np.zeros((H,W),np.uint8)
    cv2.ellipse(alpha,center,radii,angle,0,360,255,-1,cv2.LINE_AA)
    return cv2.GaussianBlur(alpha,(3,3),.6)
def png(img):
    buf=io.BytesIO();img.save(buf,format="PNG",compress_level=2);return buf.getvalue()
def produce(original,subject,output,bangs=None):
    src=np.asarray(Image.open(original).convert("RGB"))
    base=np.asarray(Image.open(subject).convert("RGBA"))
    if src.shape != (H,W,3) or base.shape != (H,W,4):
        raise ValueError("Unexpected original dimensions; refuse geometry drift")
    output.mkdir(parents=True,exist_ok=True)
    layer_dir=output/"layers";layer_dir.mkdir(parents=True,exist_ok=True)
    source_alpha=base[:,:,3]
    feature_masks={n:stencil(n) for n in PARTS}
    # Skin is sampled from the SAME picture rather than re-generating the face.
    # This is a rough hidden-surface placeholder, not a complete painted eyelid.
    yy,xx=np.mgrid[0:H,0:W]
    def skin(name):
        (ax,ay),(bx,by)=SKIN[name]
        def sample(x,y): return np.median(src[y-2:y+3,x-2:x+3],axis=(0,1))
        a,b=sample(ax,ay),sample(bx,by)
        m=np.clip((xx-ax)/max(1,bx-ax),0,1)[:,:,None]
        return np.clip(a[None,None,:]*(1-m)+b[None,None,:]*m,0,255).astype(np.uint8)
    rgb=src.copy()
    for name in ("brow_image_right","eye_image_left","eye_image_right","mouth"):
        mask=feature_masks[name].astype(np.float32)[:,:,None]/255.0
        replace=skin(name)
        rgb=np.clip(rgb.astype(np.float32)*(1-mask)+replace.astype(np.float32)*mask,0,255).astype(np.uint8)
    layers={}
    metadata=[]
    def save(name,color,mask,status,source_type):
        a=(mask.astype(np.uint16)*source_alpha.astype(np.uint16)//255).astype(np.uint8)
        rgb0=color.copy();rgb0[a==0]=0
        img=Image.fromarray(np.dstack([rgb0,a]),"RGBA")
        img.save(layer_dir/(name+".png"),compress_level=4)
        layers[name]=img
        metadata.append({"name":name,"file":"layers/"+name+".png",
          "bbox":list(img.getbbox() or (0,0,0,0)),
          "status":status,"source_pixels":source_type})
    save("00_face_underpaint",rgb,source_alpha,
      "inpainted hidden surfaces; artist must improve for rotation and expression","partly inferred skin")
    # The mostly hidden image-left brow cannot be fabricated as an independently
    # finished eyebrow; output reference but keep it hidden by default.
    save("10_brow_image_left_REFERENCE",src,feature_masks["brow_image_left"],
         "reference only, mostly occluded by bangs","original")
    save("11_brow_image_right",src,feature_masks["brow_image_right"],
         "source-aligned movable brow candidate","original")
    for suffix in ("left","right"):
        eye="eye_image_"+suffix
        iris="iris_image_"+suffix
        mask=np.minimum(feature_masks[iris],feature_masks[eye])
        # Behind iris: local inpaint of pixels so moving iris does not duplicate pupil.
        paint=cv2.inpaint(cv2.cvtColor(src,cv2.COLOR_RGB2BGR),
           cv2.dilate(np.where(mask>20,255,0).astype(np.uint8),np.ones((3,3),np.uint8)),
           2,cv2.INPAINT_TELEA)
        eye_rgb=cv2.cvtColor(paint,cv2.COLOR_BGR2RGB)
        save("20_eye_"+suffix+"_base",eye_rgb,feature_masks[eye],
             "iris-free eye/lid reference, sclera paint incomplete","partly inferred")
        save("21_iris_"+suffix,src,mask,
             "independent source-colored iris for small gaze offsets","original")
        # Lash mask: upper region only, require dark source pixels and keep the upper eyelid.
        c,r,angle=PARTS[eye]
        xs=np.arange(W)[None,:];ys=np.arange(H)[:,None]
        dark=cv2.cvtColor(src,cv2.COLOR_RGB2LAB)[:,:,0]<125
        top=ys < c[1]+2
        lash=((feature_masks[eye]>40) & dark & top).astype(np.uint8)*255
        save("22_upper_lash_"+suffix+"_REFERENCE",src,lash,
             "candidate outline only; separation includes small eyebrow/hair overlap","original")
    save("30_mouth_neutral",src,feature_masks["mouth"],
         "source lip pose; opening/teeth/tongue still need painting","original")
    # Source lip halves: useful references for artist, not deformation-ready anatomy.
    mouth=feature_masks["mouth"]
    ys=np.arange(H)[:,None]
    upper=np.where(ys<=228,mouth,0).astype(np.uint8)
    lower=np.where(ys>228,mouth,0).astype(np.uint8)
    save("31_upper_lip_REFERENCE",src,upper,"lip appearance reference, overlaps neutral mouth","original")
    save("32_lower_lip_REFERENCE",src,lower,"lip appearance reference, overlaps neutral mouth","original")
    bangs_name=None
    if bangs and Path(bangs).is_file():
        image_bangs=Image.open(bangs).convert("RGBA")
        if image_bangs.size!=(W,H):raise ValueError("Bangs canvas mismatch")
        bangs_name="40_bangs_front_REFERENCE"
        layers[bangs_name]=image_bangs
        image_bangs.save(layer_dir/(bangs_name+".png"),compress_level=4)
        metadata.append({"name":bangs_name,"file":"layers/"+bangs_name+".png",
         "bbox":list(image_bangs.getbbox() or (0,0,0,0)),
         "status":"requires precise hairline/forehead hidden art; source-aligned mask","source_pixels":"original"})
    order=["00_face_underpaint","11_brow_image_right",
       "20_eye_left_base","21_iris_left","20_eye_right_base","21_iris_right",
       "30_mouth_neutral"]
    if bangs_name:order.append(bangs_name)
    neutral=layers[order[0]].copy()
    for name in order[1:]:neutral.alpha_composite(layers[name])
    neutral.save(output/"01_face_neutral_recomposed.png",compress_level=4)
    x1,y1,x2,y2=405,151,550,254
    diff=np.abs(np.asarray(neutral.convert("RGB")).astype(np.int16)-src.astype(np.int16))
    face_diff=diff[y1:y2,x1:x2]
    mae=float(face_diff.mean())
    changed=float((np.max(face_diff,axis=2)>12).mean()*100)
    if mae>2:
        raise AssertionError(f"Original identity reconstruction changed visibly; face MAE={mae:.3f}")
    # Non-default layer poses deliberately not faked. This is a parts package, not a rig.
    doc=ET.Element("image",{"w":str(W),"h":str(H),"version":"0.0.3",
          "name":"Klika source-locked facial parts - manual repaint required"})
    stack=ET.SubElement(doc,"stack")
    extras=[name for name in layers if name not in order]
    with zipfile.ZipFile(output/"02_facial_parts_editable.ora","w") as z:
        z.writestr("mimetype","image/openraster",compress_type=zipfile.ZIP_STORED)
        for i,name in enumerate(extras+list(reversed(order))):
            filename=f"data/face_{i:02d}.png"
            # ORA stack order top to bottom: reversed list arranges base last.
            visible="visible" if name in order else "hidden"
            ET.SubElement(stack,"layer",{"name":name,"src":filename,"x":"0","y":"0",
              "opacity":"1.0","visibility":visible,"composite-op":"svg:src-over"})
            z.writestr(filename,png(layers[name]),compress_type=zipfile.ZIP_DEFLATED,compresslevel=1)
        z.writestr("mergedimage.png",png(neutral),compress_type=zipfile.ZIP_DEFLATED,compresslevel=1)
        z.writestr("stack.xml",ET.tostring(doc,encoding="utf-8",xml_declaration=True))
    report={"version":"0.5.0","source_resolution":[W,H],"face_reassembly_mean_abs_RGB_error":round(mae,3),
        "face_pixels_delta_over_12_percent":round(changed,3),
        "number_of_layers":len(layers),"cubism_model_generated":False,
        "needs_manual_paint":["Closed eyelid per side and separated lashes","White eye background behind moving iris",
          "Open mouth interior, tongue, upper/lower lip deformation shapes","Eyebrow hidden under bangs",
          "Skin and hair behind front hair and sideburns","Angle X/Y head-turn and neck/shoulder occlusions"],
        "notes":["All source-backed facial parts retain their original identity pixels",
          "Face-underpaint samples nearby skin and is not final skin artwork",
          "Do not mirror the non-symmetric eyes","All parts at full-resolution canvas coordinates"],
        "layers":metadata}
    (output/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    sheet=Image.new("RGB",(1260,600),(235,239,235));pen=ImageDraw.Draw(sheet)
    samples=[("ORIGINAL",Image.fromarray(src,"RGB")),("RECOMPOSED",neutral.convert("RGB"))]
    # Detail zoom preserving original facial proportions.
    for i,(label,img) in enumerate(samples):
        zoom=img.crop((387,115,578,268)).resize((500,405),Image.Resampling.LANCZOS)
        sx=30+i*620
        pen.rounded_rectangle((sx-10,20,sx+520,560),radius=14,fill=(250,251,248),outline=(194,207,197),width=2)
        pen.text((sx,30),label,fill=(36,57,42))
        sheet.paste(zoom,(sx,85))
    pen.text((45,535),f"MAE (facial ROI): {mae:.3f}/255 | This verifies identity at rest, NOT blink/turn rigging.",fill=(42,65,50))
    sheet.save(output/"03_identity_reassembly_check.png",compress_level=4)
    (output/"README.md").write_text(
      "# Klika v0.5 facial parts\\n\\nOriginal identity pixel source: 人设图.png.\\n"
      "Editable OpenRaster: 02_facial_parts_editable.ora\\n"
      "Separated source-backed eye bases and irises, brow, lips, fringe references.\\n"
      "Default mouth and face contours preserved; no artificial replacement personality or appearance.\\n"
      "IMPORTANT: These are candidate parts, NOT finished Cubism ArtMeshes or blinking/open-mouth drawings.\\n"
      "The incomplete facial anatomy is explicitly listed in manifest.json.\\n",
      encoding="utf-8")
    print(f"faces={len(layers)} identity_MAE={mae:.3f} output={output}")
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--subject",required=True,type=Path)
    p.add_argument("--bangs",type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    produce(a.source,a.subject,a.out,a.bangs)
