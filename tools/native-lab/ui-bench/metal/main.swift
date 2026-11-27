// AudioLab UI bench (task RN4): the same scene as ../web/scene.js, drawn with Metal.
// A 64-track arrangement scrolling at 800 px/s (clips, notes, grid, headers) and 1,000 meters
// (background, level, peak hold). One instanced draw of coloured rectangles per frame; the
// rectangles are rebuilt on the CPU every frame, as a real arrangement would.
//
// Two measurements:
//   1. "max": 3840x2160 off screen, each frame waited for (the worst case), then 3 frames in flight.
//   2. "screen": a window paced by CAMetalDisplayLink (macOS 14+), asking for up to 240 Hz,
//      for N seconds: intervals between frames, CPU time per frame, GPU time per frame.
// Output: one JSON object on stdout.
//
// Build: swiftc -O main.swift -o metalbench   Run: ./metalbench [seconds]
import Cocoa
import Metal
import QuartzCore

struct Inst { var x, y, w, h, r, g, b, a: Float }

// ---------- the scene (keep identical to ../web/scene.js) ----------
func buildScene(_ out: inout [Inst], W: Float, H: Float, t: Float) {
    out.removeAll(keepingCapacity: true)
    let ax: Float = 200, ay: Float = 40, aw = W - ax, ah = H - ay - 260
    let tracks = 64, th = ah / Float(tracks)
    let scroll = t * 800
    out.append(Inst(x: 0, y: 0, w: W, h: H, r: 0.07, g: 0.075, b: 0.09, a: 1))           // background
    // beat lines every 60 px, moving with the scroll
    var gx = ax - scroll.truncatingRemainder(dividingBy: 60)
    while gx < W { if gx >= ax { out.append(Inst(x: gx, y: ay, w: 1, h: ah, r: 0.16, g: 0.17, b: 0.2, a: 1)) }; gx += 60 }
    for tr in 0..<tracks {
        let ty = ay + Float(tr) * th
        out.append(Inst(x: ax, y: ty + th - 1, w: aw, h: 1, r: 0.12, g: 0.12, b: 0.14, a: 1)) // separator
        let P: Float = 480, cw = Float(360 + (tr % 5) * 20), off = Float((tr * 73) % 480)
        let hue = Float(tr % 8) / 8
        let kStart = Int(((scroll - off - cw) / P).rounded(.down))
        let kEnd = Int(((scroll + aw - off) / P).rounded(.down))
        if kStart > kEnd { continue }
        for k in kStart...kEnd {
            let cx = ax + off + Float(k) * P - scroll
            out.append(Inst(x: cx, y: ty + 1, w: cw, h: th - 2, r: 0.25 + 0.5 * hue, g: 0.35, b: 0.75 - 0.5 * hue, a: 0.85))
            let nw = (cw - 12) / 12
            for j in 0..<12 {
                let lane = Float((j * 7 + k * 3 + tr) % 10 + 10) .truncatingRemainder(dividingBy: 10) / 10
                out.append(Inst(x: cx + 6 + Float(j) * nw, y: ty + 2 + lane * (th - 6), w: nw - 2, h: max(2, th * 0.12),
                                r: 0.95, g: 0.95, b: 0.98, a: 0.9))
            }
        }
    }
    // track headers over the left edge
    for tr in 0..<tracks {
        let ty = ay + Float(tr) * th
        out.append(Inst(x: 0, y: ty, w: ax, h: th - 1, r: 0.11, g: 0.115, b: 0.13, a: 1))
        out.append(Inst(x: 4, y: ty + 2, w: 6, h: th - 5, r: Float(tr % 8) / 8, g: 0.6, b: 0.9, a: 1))
    }
    out.append(Inst(x: ax + aw * 0.4, y: ay, w: 2, h: ah, r: 1, g: 0.85, b: 0.3, a: 1)) // playhead
    // 1,000 meters: two rows of 500 at the bottom
    let mw = (W - 20) / 500, mh: Float = 100
    for i in 0..<1000 {
        let row = i / 500, col = i % 500
        let mx = 10 + Float(col) * mw, my = H - 250 + Float(row) * (mh + 20)
        let lv = 0.5 + 0.45 * sin(t * 7 + Float(i) * 0.37)
        let pk = min(1, lv + 0.06)
        out.append(Inst(x: mx, y: my, w: mw - 1, h: mh, r: 0.12, g: 0.12, b: 0.13, a: 1))
        out.append(Inst(x: mx, y: my + mh * (1 - lv), w: mw - 1, h: mh * lv, r: 0.3, g: 0.85, b: 0.45, a: 1))
        out.append(Inst(x: mx, y: my + mh * (1 - pk), w: mw - 1, h: 1.5, r: 1, g: 0.9, b: 0.4, a: 1))
    }
}

let shaderSrc = """
#include <metal_stdlib>
using namespace metal;
struct Inst { float4 rect; float4 col; };
struct VOut { float4 pos [[position]]; float4 col; };
vertex VOut vmain(uint vid [[vertex_id]], uint iid [[instance_id]], const device Inst* insts [[buffer(0)]], constant float2& vp [[buffer(1)]]) {
  float2 c[6] = { float2(0,0), float2(1,0), float2(0,1), float2(1,0), float2(1,1), float2(0,1) };
  Inst it = insts[iid];
  float2 p = it.rect.xy + c[vid] * it.rect.zw;
  VOut o; o.pos = float4(p.x / vp.x * 2 - 1, 1 - p.y / vp.y * 2, 0, 1); o.col = float4(it.col.rgb * it.col.a, it.col.a); return o;
}
fragment float4 fmain(VOut in [[stage_in]]) { return in.col; }
"""

func stats(_ v: [Double]) -> [String: Double] {
    if v.isEmpty { return [:] }
    let s = v.sorted()
    func q(_ p: Double) -> Double { s[min(s.count - 1, Int(Double(s.count - 1) * p))] }
    return ["n": Double(s.count), "median": q(0.5), "p95": q(0.95), "p99": q(0.99), "worst": s.last!, "mean": s.reduce(0, +) / Double(s.count)]
}

guard let dev = MTLCreateSystemDefaultDevice() else { print("{\"error\":\"no Metal device\"}"); exit(1) }
let lib = try! dev.makeLibrary(source: shaderSrc, options: nil)
let pd = MTLRenderPipelineDescriptor()
pd.vertexFunction = lib.makeFunction(name: "vmain"); pd.fragmentFunction = lib.makeFunction(name: "fmain")
pd.colorAttachments[0].pixelFormat = .bgra8Unorm
pd.colorAttachments[0].isBlendingEnabled = true
pd.colorAttachments[0].sourceRGBBlendFactor = .one; pd.colorAttachments[0].destinationRGBBlendFactor = .oneMinusSourceAlpha
pd.colorAttachments[0].sourceAlphaBlendFactor = .one; pd.colorAttachments[0].destinationAlphaBlendFactor = .oneMinusSourceAlpha
let pipe = try! dev.makeRenderPipelineState(descriptor: pd)
let queue = dev.makeCommandQueue()!
let maxInst = 40000
let bufs = (0..<3).map { _ in dev.makeBuffer(length: maxInst * MemoryLayout<Inst>.stride, options: .storageModeShared)! }
var scene: [Inst] = []; scene.reserveCapacity(maxInst)

/// encodes one frame into `tex`; returns (cpu ms to build+encode, instance count)
func encode(_ cb: MTLCommandBuffer, tex: MTLTexture, buf: MTLBuffer, t: Float) -> (Double, Int) {
    let t0 = CACurrentMediaTime()
    let W = Float(tex.width), H = Float(tex.height)
    buildScene(&scene, W: W, H: H, t: t)
    let n = min(scene.count, maxInst)
    scene.withUnsafeBytes { raw in buf.contents().copyMemory(from: raw.baseAddress!, byteCount: n * MemoryLayout<Inst>.stride) }
    let rp = MTLRenderPassDescriptor()
    rp.colorAttachments[0].texture = tex; rp.colorAttachments[0].loadAction = .clear
    rp.colorAttachments[0].clearColor = MTLClearColor(red: 0, green: 0, blue: 0, alpha: 1); rp.colorAttachments[0].storeAction = .store
    let enc = cb.makeRenderCommandEncoder(descriptor: rp)!
    enc.setRenderPipelineState(pipe)
    enc.setVertexBuffer(buf, offset: 0, index: 0)
    var vp = SIMD2<Float>(W, H); enc.setVertexBytes(&vp, length: 8, index: 1)
    enc.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 6, instanceCount: n)
    enc.endEncoding()
    return ((CACurrentMediaTime() - t0) * 1000, n)
}

var result: [String: Any] = ["renderer": "Metal", "device": dev.name]
let seconds = Double(CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "10") ?? 10

// ---------- 1. max, off screen at 3840x2160 ----------
do {
    let td = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .bgra8Unorm, width: 3840, height: 2160, mipmapped: false)
    td.usage = [.renderTarget]; td.storageMode = .private
    let tex = dev.makeTexture(descriptor: td)!
    var wall: [Double] = [], cpu: [Double] = [], gpu: [Double] = []; var inst = 0
    for i in 0..<360 {                       // waited for, one at a time
        let t0 = CACurrentMediaTime()
        let cb = queue.makeCommandBuffer()!
        let (c, n) = encode(cb, tex: tex, buf: bufs[0], t: Float(i) / 240)
        cb.commit(); cb.waitUntilCompleted()
        if i >= 60 { wall.append((CACurrentMediaTime() - t0) * 1000); cpu.append(c); gpu.append((cb.gpuEndTime - cb.gpuStartTime) * 1000) }
        inst = n
    }
    // three in flight: throughput
    let sem = DispatchSemaphore(value: 3)
    let tp0 = CACurrentMediaTime(); let N = 600
    for i in 0..<N {
        sem.wait()
        let cb = queue.makeCommandBuffer()!
        _ = encode(cb, tex: tex, buf: bufs[i % 3], t: Float(i) / 240)
        cb.addCompletedHandler { _ in sem.signal() }
        cb.commit()
    }
    for _ in 0..<3 { sem.wait() }
    let fps = Double(N) / (CACurrentMediaTime() - tp0)
    result["max_3840x2160"] = ["rects": inst, "frame_waited_ms": stats(wall), "cpu_build_encode_ms": stats(cpu), "gpu_ms": stats(gpu), "pipelined_fps": fps]
}

// ---------- 2. on screen, paced by CAMetalDisplayLink ----------
final class Screen: NSObject, CAMetalDisplayLinkDelegate {
    var link: CAMetalDisplayLink!
    var start = 0.0, last = 0.0
    var intervals: [Double] = [], cpu: [Double] = [], gpu: [Double] = [], lateness: [Double] = []
    let lock = NSLock(); var frame = 0; var size = CGSize.zero
    func metalDisplayLink(_ link: CAMetalDisplayLink, needsUpdate update: CAMetalDisplayLink.Update) {
        let now = CACurrentMediaTime()
        if start == 0 { start = now }
        if last != 0 { intervals.append((now - last) * 1000) }
        last = now
        let drawable = update.drawable
        let cb = queue.makeCommandBuffer()!
        let (c, _) = encode(cb, tex: drawable.texture, buf: bufs[frame % 3], t: Float(update.targetTimestamp - start))
        cpu.append(c); frame += 1
        let target = update.targetPresentationTimestamp
        cb.addCompletedHandler { [weak self] b in
            guard let self = self else { return }
            self.lock.lock(); self.gpu.append((b.gpuEndTime - b.gpuStartTime) * 1000)
            self.lateness.append((b.gpuEndTime - target) * 1000); self.lock.unlock()
        }
        cb.present(drawable); cb.commit()
        size = CGSize(width: drawable.texture.width, height: drawable.texture.height)
        if now - start > seconds { finish() }
    }
    func finish() {
        link.invalidate()
        lock.lock(); let g = gpu; let late = lateness; lock.unlock()
        let budget = 1000.0 / Double(NSScreen.main?.maximumFramesPerSecond ?? 60)
        let missed = intervals.filter { $0 > budget * 1.5 }.count
        result["screen"] = ["screen_max_fps": NSScreen.main?.maximumFramesPerSecond ?? 0,
                            "drawable": "\(Int(size.width))x\(Int(size.height))",
                            "frames": frame, "fps": last > start ? Double(frame) / (last - start) : 0,
                            "interval_ms": stats(intervals), "missed_frames_over_1_5x": missed,
                            "cpu_build_encode_ms": stats(cpu), "gpu_ms": stats(g),
                            "gpu_end_minus_target_ms": stats(late)]
        let data = try! JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
        print(String(data: data, encoding: .utf8)!)
        fflush(stdout); exit(0)
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.regular)
let win = NSWindow(contentRect: NSRect(x: 40, y: 40, width: 1600, height: 1000), styleMask: [.titled, .closable], backing: .buffered, defer: false)
win.title = "AudioLab UI bench (Metal)"
let view = NSView(frame: win.contentLayoutRect)
view.wantsLayer = true
let ml = CAMetalLayer()
ml.device = dev; ml.pixelFormat = .bgra8Unorm; ml.framebufferOnly = true; ml.maximumDrawableCount = 3
ml.contentsScale = win.backingScaleFactor
view.layer = ml
win.contentView = view
ml.drawableSize = CGSize(width: view.bounds.width * win.backingScaleFactor, height: view.bounds.height * win.backingScaleFactor)
win.makeKeyAndOrderFront(nil)
app.activate(ignoringOtherApps: true)
let screen = Screen()
screen.link = CAMetalDisplayLink(metalLayer: ml)
screen.link.preferredFrameRateRange = CAFrameRateRange(minimum: 60, maximum: 240, preferred: 240)
screen.link.delegate = screen
screen.link.add(to: .main, forMode: .common)
DispatchQueue.main.asyncAfter(deadline: .now() + seconds + 20) {   // safety net if the link never fires
    if screen.frame == 0 { result["screen"] = ["error": "display link never fired"] ; screen.finish() } else { screen.finish() }
}
app.run()
