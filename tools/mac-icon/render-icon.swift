// Draws the icon macOS itself shows for a file (NSWorkspace) into a PNG: render-icon <path> <out.png> [pixels]
// Used by the workflows to look at the app icon on the macOS runner (task IC1).
import AppKit
let a = CommandLine.arguments
guard a.count >= 3 else { print("usage: render-icon <path> <out.png> [pixels]"); exit(2) }
let px = a.count > 3 ? Int(a[3]) ?? 512 : 512
let img = NSWorkspace.shared.icon(forFile: a[1])
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: px, pixelsHigh: px, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
rep.size = NSSize(width: px, height: px)
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
img.draw(in: NSRect(x: 0, y: 0, width: px, height: px), from: .zero, operation: .copy, fraction: 1)
NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: a[2]))
// The tile colour at a spot that is plain blue in the W7 picture (35 % from the left, 14 % from the top), averaged over 9 x 9 pixels.
var r = 0.0, g = 0.0, b = 0.0, n = 0.0
let cx = Int(Double(px) * 0.3516), cy = Int(Double(px) * 0.1406)
for y in (cy - 4)...(cy + 4) { for x in (cx - 4)...(cx + 4) { if let c = rep.colorAt(x: x, y: y) { r += Double(c.redComponent); g += Double(c.greenComponent); b += Double(c.blueComponent); n += 1 } } }
print("TILE \(Int((r / n * 255).rounded())) \(Int((g / n * 255).rounded())) \(Int((b / n * 255).rounded()))")
print("wrote \(a[2]) \(px) px, reps of the system image: \(img.representations.map { "\($0.pixelsWide)x\($0.pixelsHigh)" }.joined(separator: " "))")
