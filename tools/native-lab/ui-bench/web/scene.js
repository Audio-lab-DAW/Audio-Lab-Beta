// AudioLab UI bench (task RN4): the scene, identical to ../metal/main.swift buildScene().
// Fills `out` (Float32Array, 8 floats per rectangle: x y w h r g b a) and returns the count.
function buildScene(out, W, H, t) {
  let n = 0;
  const put = (x, y, w, h, r, g, b, a) => { const o = n * 8; out[o] = x; out[o + 1] = y; out[o + 2] = w; out[o + 3] = h; out[o + 4] = r; out[o + 5] = g; out[o + 6] = b; out[o + 7] = a; n++; };
  const ax = 200, ay = 40, aw = W - ax, ah = H - ay - 260;
  const tracks = 64, th = ah / tracks;
  const scroll = t * 800;
  put(0, 0, W, H, 0.07, 0.075, 0.09, 1);
  for (let gx = ax - (scroll % 60); gx < W; gx += 60) if (gx >= ax) put(gx, ay, 1, ah, 0.16, 0.17, 0.2, 1);
  for (let tr = 0; tr < tracks; tr++) {
    const ty = ay + tr * th;
    put(ax, ty + th - 1, aw, 1, 0.12, 0.12, 0.14, 1);
    const P = 480, cw = 360 + (tr % 5) * 20, off = (tr * 73) % 480, hue = (tr % 8) / 8;
    const kStart = Math.floor((scroll - off - cw) / P), kEnd = Math.floor((scroll + aw - off) / P);
    for (let k = kStart; k <= kEnd; k++) {
      const cx = ax + off + k * P - scroll;
      put(cx, ty + 1, cw, th - 2, 0.25 + 0.5 * hue, 0.35, 0.75 - 0.5 * hue, 0.85);
      const nw = (cw - 12) / 12;
      for (let j = 0; j < 12; j++) {
        const lane = (((j * 7 + k * 3 + tr) % 10 + 10) % 10) / 10;
        put(cx + 6 + j * nw, ty + 2 + lane * (th - 6), nw - 2, Math.max(2, th * 0.12), 0.95, 0.95, 0.98, 0.9);
      }
    }
  }
  for (let tr = 0; tr < tracks; tr++) {
    const ty = ay + tr * th;
    put(0, ty, ax, th - 1, 0.11, 0.115, 0.13, 1);
    put(4, ty + 2, 6, th - 5, (tr % 8) / 8, 0.6, 0.9, 1);
  }
  put(ax + aw * 0.4, ay, 2, ah, 1, 0.85, 0.3, 1);
  const mw = (W - 20) / 500, mh = 100;
  for (let i = 0; i < 1000; i++) {
    const row = Math.floor(i / 500), col = i % 500;
    const mx = 10 + col * mw, my = H - 250 + row * (mh + 20);
    const lv = 0.5 + 0.45 * Math.sin(t * 7 + i * 0.37), pk = Math.min(1, lv + 0.06);
    put(mx, my, mw - 1, mh, 0.12, 0.12, 0.13, 1);
    put(mx, my + mh * (1 - lv), mw - 1, mh * lv, 0.3, 0.85, 0.45, 1);
    put(mx, my + mh * (1 - pk), mw - 1, 1.5, 1, 0.9, 0.4, 1);
  }
  return n;
}
