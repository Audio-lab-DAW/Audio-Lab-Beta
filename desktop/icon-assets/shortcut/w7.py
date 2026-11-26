exec(open('/home/claude/gen/assets2.py').read().split('# main files')[0])
exec(open('/home/claude/gen/zoom.py').read().split('T={')[0].split('exec(',1)[1].split('\n',1)[1])
A2="/home/claude/w7/"; shutil.rmtree(A2,ignore_errors=True); os.makedirs(A2)
def w7_inner(t):
    kw=dict(TIERS[t][0]); s=1.5; keep=.85 if t=="L" else .7
    kw["ring_w"]*=keep; kw["gap"]*=max(keep,.8)
    trt=place(TIERS[t][0],1.0,(512,504)); ttx,tty=map(float,re.findall(r"translate\(([-\d.]+) ([-\d.]+)\)",trt)[0])
    ex_,ey_=ell(360,150,-30,0.0); ex_+=ttx; ey_+=tty
    et=(800,190); X,Y=et[0]-ex_*s,et[1]-ey_*s
    els=list(mark(W,OC,**kw)); els[-1]=els[-1].replace(f'fill="{W}"',f'fill="{YE}"',1); els[-3]=els[-3].replace(f'fill="{W}"',f'fill="{YE}"',1)
    return f'<defs><clipPath id="c"><rect width="1024" height="1024" rx="230"/></clipPath></defs><rect width="1024" height="1024" rx="230" fill="{OC}"/><g clip-path="url(#c)"><g transform="rotate(-6 800 190)"><g transform="translate({X:.1f} {Y:.1f}) scale({s}) {trt}">{"".join(els)}</g></g></g>'
def W7full(t): return f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">{w7_inner(t)}</svg>'
def W7grid(t): return f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024"><defs><filter id="sh" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity="0.28"/></filter></defs><rect x="100" y="100" width="824" height="824" rx="185" fill="{OC}" filter="url(#sh)"/><g transform="translate(100 100) scale(0.8046875)">{w7_inner(t)}</g></svg>'
# size plan: 16-20 px normal XS (zoom unreadable there), 24-512 px W7, 1024 px normal (large)
def pick_fn(zoomfn,normfn):
    def f(s): return normfn(tier(s)) if (s<24 or s>=1024) else zoomfn(tier(s))
    return f
def icns2(f,out):
    ch=b""
    for t,s in (("icp4",16),("icp5",32),("ic11",32),("ic12",64),("ic07",128),("ic13",256),("ic08",256),("ic14",512),("ic09",512),("ic10",1024)):
        d=png_bytes(f(s),s); ch+=t.encode()+struct.pack(">I",len(d)+8)+d
    open(out,"wb").write(b"icns"+struct.pack(">I",len(ch)+8)+ch)
def ico2(f,out,sizes=(16,20,24,32,40,48,64,96,128,256)):
    imgs=[png_bytes(f(s),s) for s in sizes]; hdr=struct.pack("<HHH",0,1,len(sizes)); off=6+16*len(sizes); ent=b""
    for s,d in zip(sizes,imgs): ent+=struct.pack("<BBBBHHII",s%256,s%256,0,0,1,32,len(d),off); off+=len(d)
    open(out,"wb").write(hdr+ent+b"".join(imgs))
icns2(pick_fn(W7grid,grid),A2+"icon.icns"); ico2(pick_fn(W7full,full),A2+"icon.ico")
open(A2+"dock-icon.png","wb").write(png_bytes(W7grid("L"),1024))
for t in ("L","M","S"): open(A2+f"shortcut-{t}.svg","w").write(W7full(t)); open(A2+f"shortcut-{t}.png","wb").write(png_bytes(W7full(t),1024))
from PIL import Image, ImageDraw
sh=Image.new("RGB",(980,300),(30,30,36)); d=ImageDraw.Draw(sh); x=10
for s in (256,128,64,48,32,24,20,16):
    im=Image.open(io.BytesIO(png_bytes(pick_fn(W7grid,grid)(s),s))).convert("RGBA"); sh.paste(im,(x,20),im); d.text((x,24+s),str(s),fill=(200,200,200)); x+=s+14
sh.save("/home/claude/w7_sizes.png")
