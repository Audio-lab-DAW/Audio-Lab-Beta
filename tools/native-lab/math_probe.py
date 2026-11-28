"""Which maths functions does the browser's JavaScript use? (task NB-N3c)

Runs headless Chromium, works out Math.sin, cos, exp, pow and log10 (and, task NB-N3j, log and tanh) on 400,000 arguments of the kinds the
ported devices use (phases times 2 pi, levels in dB, small negative exponents), and writes them with the
arguments to <out>/math_vals.bin. `almathprobe <out>/math_vals.bin` (native/engine/math_probe.cpp) then counts
the differences against the engine's own functions (js:: in jsmath.h) and against the system's library.

    python3 tools/native-lab/math_probe.py <outdir>
"""
import base64, os, sys
from playwright.sync_api import sync_playwright

JS = """() => { const TAU=Math.PI*2, N=400000, out=new Float64Array(N*12); let ph=0, x=0.37;
 for (let i=0;i<N;i++){ ph=(ph+0.4/48000)%1; const a=TAU*ph; x=(x*1103.515245+0.12345)%1; const d=x*40-20, l=x*3+1e-6;
   out[8*i]=a; out[8*i+1]=Math.sin(a); out[8*i+2]=Math.cos(a); out[8*i+3]=d; out[8*i+4]=Math.pow(10,d/20); out[8*i+5]=Math.exp(-d/7);
   out[8*i+6]=l; out[8*i+7]=Math.log10(l); }
 for (let i=0;i<N;i++){ x=(x*1103.515245+0.12345)%1; const la=20+x*15000, t=(x-.5)*6; out[8*N+4*i]=la; out[8*N+4*i+1]=Math.log(la); out[8*N+4*i+2]=t; out[8*N+4*i+3]=Math.tanh(t); }   // task NB-N3j: Math.log, Math.tanh
 const u=new Uint8Array(out.buffer); let s=''; for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));
 return [btoa(s), navigator.userAgent] }"""


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); r = pg.evaluate(JS); b.close()
    open(os.path.join(out, "math_vals.bin"), "wb").write(base64.b64decode(r[0]))
    print("browser:", r[1])


if __name__ == "__main__":
    main()
