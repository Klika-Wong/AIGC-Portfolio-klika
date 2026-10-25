#!/usr/bin/env python3
"""Identity-preserving mask extraction from the repository ORIGINAL image.
Outputs transparent candidate regions + OpenRaster. NOT a rigged Cubism model.
"""
import argparse,io,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw

# Region polygons are *reference selection*, not isolated professional Live2D artwork.
REGIONS={
"hair_back_left":[(180,135),(363,78),(405,160),(370,420),(335,680),(335,970),(150,860),(175,520)],
"hair_back_right":[(535,76),(635,136),(820,440),(855,840),(750,940),(615,650),(586,340)],
"hair_bangs":[(368,29),(570,22),(600,145),(546,210),(412,218),(344,166)],
"hair_side_left":[(345,144),(450,195),(426,469),(337,702),(218,872),(196,718),(303,354)],
"hair_side_right":[(549,137),(652,198),(717,415),(796,765),(747,939),(662,744),(573,448)],
"face_base":[(402,135),(562,133),(570,266),(515,302),(443,296),(409,246)],
"eye_left_source":[(412,165),(489,160),(494,204),(422,212)],
"eye_right_source":[(483,155),(550,155),(559,198),(488,208)],
"brows_source":[(418,149),(552,139),(563,174),(417,186)],
"mouth_source":[(450,230),(512,226),(515,266),(444,267)],
"neck_source":[(446,269),(551,252),(576,349),(433,357)],
"top":[(410,284),(620,292),(652,497),(603,576),(400,577),(369,449)],
"jacket_left":[(313,366),(414,399),(414,648),(357,913),(234,912),(248,527)],
"jacket_right":[(634,386),(715,401),(801,667),(754,947),(624,926),(605,608)],
"hand_raised":[(320,362),(425,322),(501,329),(516,382),(421,413),(370,491),(308,474)],
"hand_down":[(701,841),(755,855),(753,1015),(669,1020),(679,893)],
"bracelet":[(324,401),(410,385),(421,488),(327,510),(307,440)],
"pendulum":[(457,317),(510,323),(519,436),(454,434)],
"abdomen":[(409,552),(603,560),(627,660),(380,656)],
"pants":[(349,616),(640,609),(724,1190),(593,1260),(531,1044),(495,1240),(368,1217),(313,699)],
"flip_phone":[(522,660),(611,665),(634,757),(533,771)],
"small_box":[(654,677),(746,665),(760,802),(649,806)],
"boot_left":[(379,1125),(511,1114),(551,1498),(353,1521)],
"boot_right":[(609,1124),(759,1113),(837,1532),(654,1534)]
}

def png(img):
    f=io.BytesIO();img.save(f,format='PNG',compress_level=2);return f.getvalue()

def foreground(src):
    arr=np.asarray(src.convert('RGB'),dtype=np.uint8);h,w=arr.shape[:2]
    v=arr.astype(np.float32)
    left=np.median(v[:,3:35],axis=1);right=np.median(v[:,w-35:w-3],axis=1)
    x=np.linspace(0,1,w,dtype=np.float32)[None,:,None]
    delta=np.linalg.norm(v-(left[:,None,:]*(1-x)+right[:,None,:]*x),axis=2)
    mask=np.full((h,w),cv2.GC_PR_BGD,np.uint8)
    mask[delta>24]=cv2.GC_PR_FGD;mask[delta>57]=cv2.GC_FGD;mask[delta<13]=cv2.GC_BGD
    m=max(6,int(w*.055))
    mask[:max(10,int(h*.009)),:]=0;mask[-max(10,int(h*.007)):,:]=0
    mask[:,:m]=0;mask[:,-m:]=0
    cv2.grabCut(cv2.cvtColor(arr,cv2.COLOR_RGB2BGR),mask,None,np.zeros((1,65),np.float64),np.zeros((1,65),np.float64),3,cv2.GC_INIT_WITH_MASK)
    alpha=np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD),255,0).astype(np.uint8)
    ys=np.indices((h,w))[0];alpha[(ys>h*.927)&(arr.mean(axis=2)>84)]=0
    alpha=cv2.morphologyEx(alpha,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    n,ids,stats,_=cv2.connectedComponentsWithStats(alpha,8)
    out=np.zeros_like(alpha)
    for i in range(1,n):
        if stats[i,cv2.CC_STAT_AREA]>=max(30,int(h*w*.000035)):out[ids==i]=255
    return cv2.GaussianBlur(out,(3,3),.45)

def maskpoly(h,w,pts):
    out=np.zeros((h,w),np.uint8)
    coords=np.array([(round(x*w/1024),round(y*h/1536)) for x,y in pts],np.int32)
    cv2.fillPoly(out,[coords],255)
    return cv2.GaussianBlur(out,(3,3),.48)

def create(source,out):
    src=Image.open(source).convert('RGB');w,h=src.size
    if w<600 or h<900 or not .55<w/h<.85:
        raise ValueError('Portrait layout changed. Refuse unsafe pre-set region coordinates.')
    out.mkdir(parents=True,exist_ok=True);(out/'layers').mkdir(exist_ok=True)
    rgb=np.asarray(src);alpha=foreground(src)
    subject=Image.fromarray(np.dstack([rgb,alpha]),'RGBA')
    subject.save(out/'00_subject_cutout.png',compress_level=2)
    images=[];manifest=[]
    for name,pts in REGIONS.items():
        roi=maskpoly(h,w,pts)
        a=(alpha.astype(np.uint16)*roi.astype(np.uint16)//255).astype(np.uint8)
        rgba=rgb.copy();rgba[a==0]=0
        img=Image.fromarray(np.dstack([rgba,a]),'RGBA')
        img.save(out/'layers'/f'{name}.png',compress_level=2)
        images.append((name,img))
        manifest.append({'name':name,'file':f'layers/{name}.png','bbox':list(img.getbbox() or (0,0,0,0)),'pixel_count':int(np.count_nonzero(a)), 'status':'transparent ROI candidate; needs paint/rig'})
    cols=4;cw=220;ch=260;rows=(len(images)+cols-1)//cols
    sheet=Image.new('RGB',(cols*cw,rows*ch),(240,241,239));pen=ImageDraw.Draw(sheet)
    for idx,(name,img) in enumerate(images):
        bounds=img.getbbox()
        if bounds:
            t=img.crop(bounds);t.thumbnail((205,215),Image.Resampling.LANCZOS)
            tx=(idx%cols)*cw+(cw-t.width)//2;ty=(idx//cols)*ch+(220-t.height)//2
            sheet.paste(t,(tx,ty),t)
        pen.text(((idx%cols)*cw+10,(idx//cols)*ch+230),name,fill=(36,38,37))
    sheet.save(out/'01_parts_inventory.png')
    root=ET.Element('image',{'w':str(w),'h':str(h),'version':'0.0.3','name':'Klika original reference cutout (NOT Cubism)'})
    stack=ET.SubElement(root,'stack')
    with zipfile.ZipFile(out/'02_editable_reference.ora','w') as z:
        z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
        for j,(name,img) in enumerate(reversed(images)):
            fn=f'data/{j:02d}.png'
            ET.SubElement(stack,'layer',{'name':name+' [needs manual repair]','src':fn,'x':'0','y':'0','opacity':'1.0','visibility':'hidden','composite-op':'svg:src-over'})
            z.writestr(fn,png(img),compress_type=zipfile.ZIP_DEFLATED,compresslevel=1)
        ET.SubElement(stack,'layer',{'name':'source cutout - identity anchor','src':'data/base.png','x':'0','y':'0','opacity':'1.0','visibility':'visible','composite-op':'svg:src-over'})
        z.writestr('data/base.png',png(subject),compress_type=zipfile.ZIP_DEFLATED,compresslevel=1)
        z.writestr('mergedimage.png',png(subject),compress_type=zipfile.ZIP_DEFLATED,compresslevel=1)
        z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True))
    (out/'manifest.json').write_text(json.dumps({'version':'0.3.0','source_image':str(source),'resolution':[w,h],
       'number_of_reference_regions':len(images),'cubism_model_generated':False,
       'warnings':['Parts overlap and may contain neighbouring regions; not ready for mesh deformation',
                   'Occluded areas of face, eye interior, mouth interior and jacket require repainting'],
       'parts':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'README.md').write_text(
      '# 原始人设 Live2D 透明分区素材 v0.3\\n\\n以原始人设图制作，不重绘、不换脸、不换发型。\\n\\n'
      '- 00_subject_cutout.png：透明人物主体（需修发丝和边缘）\\n'
      '- layers/*.png：24 个真实透明 RGBA 分区候选，不是最终可绑定部件\\n'
      '- 01_parts_inventory.png：部件预览\\n'
      '- 02_editable_reference.ora：Krita/GIMP 可打开的分层文件，候选层默认隐藏；可转 PSD\\n'
      '- manifest.json：分区边界和质量说明\\n\\n'
      '**现阶段不能直接导出 .moc3**：没有补画遮挡区域，眼和口缺乏闭合形态，需要在 Cubism 中完成网格、变形器、绑定、物理模拟和导出。\\n',encoding='utf-8')
    print(f'Generated {len(images)} candidates: {out}')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();create(a.source,a.out)
