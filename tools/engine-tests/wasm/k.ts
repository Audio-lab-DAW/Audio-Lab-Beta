// benchmark kernel: NV voices, each NO polyBLEP saws -> stereo biquad low-pass -> envelope, written into L/R
const NV: i32 = 8, NO: i32 = 7;
const ph = new StaticArray<f64>(NV*NO), df = new StaticArray<f64>(NV*NO), gl = new StaticArray<f32>(NV*NO), gr = new StaticArray<f32>(NV*NO);
const z = new StaticArray<f64>(NV*4);
export const L = new StaticArray<f32>(2048), R = new StaticArray<f32>(2048);
export function lptr(): usize { return changetype<usize>(L) }
export function rptr(): usize { return changetype<usize>(R) }
export function init(sr: f64): void {
  for (let v = 0; v < NV; v++) for (let o = 0; o < NO; o++) { const i = v*NO+o; ph[i] = 0.5; const f = 110.0*Math.pow(2.0, f64(v*3)/12.0)*Math.pow(2.0, (f64(o)/6.0*2.0-1.0)*28.0/1200.0); df[i] = f/sr; gl[i] = f32(0.26*(0.3+f64(o)/10.0)); gr[i] = f32(0.26*(1.0-f64(o)/10.0)); }
}
export function run(n: i32, b0: f64, b1: f64, a1: f64, a2: f64, e: f64): void {
  for (let i = 0; i < n; i++) { unchecked(L[i] = 0); unchecked(R[i] = 0); }
  for (let v = 0; v < NV; v++) {
    let z1l = unchecked(z[v*4]), z2l = unchecked(z[v*4+1]), z1r = unchecked(z[v*4+2]), z2r = unchecked(z[v*4+3]);
    for (let i = 0; i < n; i++) {
      let xl: f64 = 0, xr: f64 = 0;
      for (let o = 0; o < NO; o++) { const k = v*NO+o; let t = unchecked(ph[k]); const d = unchecked(df[k]); let s = 2.0*t-1.0;
        if (t < d) { const x = t/d; s -= 2.0*x-x*x-1.0 } else if (t > 1.0-d) { const x = (t-1.0)/d; s -= x*x+2.0*x+1.0 }
        t += d; if (t >= 1.0) t -= 1.0; unchecked(ph[k] = t); xl += s*f64(unchecked(gl[k])); xr += s*f64(unchecked(gr[k])); }
      const yl = b0*xl+z1l; z1l = b1*xl-a1*yl+z2l; z2l = b0*xl-a2*yl; const yr = b0*xr+z1r; z1r = b1*xr-a1*yr+z2r; z2r = b0*xr-a2*yr;
      unchecked(L[i] += f32(yl*e)); unchecked(R[i] += f32(yr*e));
    }
    unchecked(z[v*4] = z1l); unchecked(z[v*4+1] = z2l); unchecked(z[v*4+2] = z1r); unchecked(z[v*4+3] = z2r);
  }
}
