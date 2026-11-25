// alvol: tiny Core Audio helper for AudioLab Studio (macOS).
//   alvol list              -> JSON: default output uid + output devices with hardware-volume info
//   alvol get <uid>         -> JSON: {"uid":..,"volume":0..1}
//   alvol set <uid> <0..1>  -> JSON: {"ok":true,"volume":..}
//   alvol info              -> JSON: every device (inputs too): kind of connection, channels, sample rate, rates on offer, bit depth, exclusive use
//   alvol rate <uid> <hz>   -> JSON: {"ok":true,"rate":..}  sets the device's own sample rate
import CoreAudio
import Foundation

let SYS = AudioObjectID(kAudioObjectSystemObject)
func addr(_ s: AudioObjectPropertySelector, _ sc: AudioObjectPropertyScope = kAudioObjectPropertyScopeGlobal, _ el: UInt32 = 0) -> AudioObjectPropertyAddress {
  AudioObjectPropertyAddress(mSelector: s, mScope: sc, mElement: el)
}
func devices() -> [AudioDeviceID] {
  var a = addr(kAudioHardwarePropertyDevices); var size: UInt32 = 0
  guard AudioObjectGetPropertyDataSize(SYS, &a, 0, nil, &size) == noErr else { return [] }
  var ids = [AudioDeviceID](repeating: 0, count: Int(size) / MemoryLayout<AudioDeviceID>.size)
  guard AudioObjectGetPropertyData(SYS, &a, 0, nil, &size, &ids) == noErr else { return [] }
  return ids
}
func cfString(_ id: AudioObjectID, _ sel: AudioObjectPropertySelector) -> String {
  var a = addr(sel); var ref: Unmanaged<CFString>? = nil
  var size = UInt32(MemoryLayout<Unmanaged<CFString>?>.size)
  guard AudioObjectGetPropertyData(id, &a, 0, nil, &size, &ref) == noErr, let r = ref else { return "" }
  return r.takeRetainedValue() as String
}
func isOutput(_ id: AudioDeviceID) -> Bool {
  var a = addr(kAudioDevicePropertyStreams, kAudioDevicePropertyScopeOutput); var size: UInt32 = 0
  return AudioObjectGetPropertyDataSize(id, &a, 0, nil, &size) == noErr && size > 0
}
func defaultOutput() -> AudioDeviceID {
  var a = addr(kAudioHardwarePropertyDefaultOutputDevice); var id = AudioDeviceID(0)
  var size = UInt32(MemoryLayout<AudioDeviceID>.size)
  AudioObjectGetPropertyData(SYS, &a, 0, nil, &size, &id); return id
}
// volume elements that can be set: main element first, else the first two channels
func volElements(_ id: AudioDeviceID) -> [UInt32] {
  for set in [[UInt32(0)], [1, 2], [1]] {
    var ok = true
    for el in set {
      var a = addr(kAudioDevicePropertyVolumeScalar, kAudioDevicePropertyScopeOutput, el)
      var settable: DarwinBoolean = false
      if !AudioObjectHasProperty(id, &a) || AudioObjectIsPropertySettable(id, &a, &settable) != noErr || !settable.boolValue { ok = false; break }
    }
    if ok { return set }
  }
  return []
}
func getVol(_ id: AudioDeviceID) -> Float? {
  let els = volElements(id); if els.isEmpty { return nil }
  var sum: Float = 0
  for el in els {
    var a = addr(kAudioDevicePropertyVolumeScalar, kAudioDevicePropertyScopeOutput, el)
    var v = Float32(0); var size = UInt32(MemoryLayout<Float32>.size)
    AudioObjectGetPropertyData(id, &a, 0, nil, &size, &v); sum += v
  }
  return sum / Float(els.count)
}
func setVol(_ id: AudioDeviceID, _ v: Float) -> Bool {
  let els = volElements(id); if els.isEmpty { return false }
  var ok = true
  for el in els {
    var a = addr(kAudioDevicePropertyVolumeScalar, kAudioDevicePropertyScopeOutput, el)
    var x = Float32(max(0, min(1, v)))
    if AudioObjectSetPropertyData(id, &a, 0, nil, UInt32(MemoryLayout<Float32>.size), &x) != noErr { ok = false }
  }
  return ok
}
func byUID(_ uid: String) -> AudioDeviceID? {
  if uid == "default" { return defaultOutput() }
  return devices().first { cfString($0, kAudioDevicePropertyDeviceUID) == uid }
}
func defaultInput() -> AudioDeviceID {
  var a = addr(kAudioHardwarePropertyDefaultInputDevice); var id = AudioDeviceID(0)
  var size = UInt32(MemoryLayout<AudioDeviceID>.size)
  AudioObjectGetPropertyData(SYS, &a, 0, nil, &size, &id); return id
}
func u32(_ id: AudioObjectID, _ sel: AudioObjectPropertySelector, _ sc: AudioObjectPropertyScope = kAudioObjectPropertyScopeGlobal) -> UInt32? {
  var a = addr(sel, sc); var v = UInt32(0); var size = UInt32(MemoryLayout<UInt32>.size)
  guard AudioObjectHasProperty(id, &a), AudioObjectGetPropertyData(id, &a, 0, nil, &size, &v) == noErr else { return nil }
  return v
}
func nominalRate(_ id: AudioDeviceID) -> Double {
  var a = addr(kAudioDevicePropertyNominalSampleRate); var v = Float64(0); var size = UInt32(MemoryLayout<Float64>.size)
  guard AudioObjectGetPropertyData(id, &a, 0, nil, &size, &v) == noErr else { return 0 }
  return v
}
func channels(_ id: AudioDeviceID, _ sc: AudioObjectPropertyScope) -> Int {
  var a = addr(kAudioDevicePropertyStreamConfiguration, sc); var size: UInt32 = 0
  guard AudioObjectGetPropertyDataSize(id, &a, 0, nil, &size) == noErr, size > 0 else { return 0 }
  let p = UnsafeMutableRawPointer.allocate(byteCount: Int(size), alignment: MemoryLayout<AudioBufferList>.alignment)
  defer { p.deallocate() }
  guard AudioObjectGetPropertyData(id, &a, 0, nil, &size, p) == noErr else { return 0 }
  let list = UnsafeMutableAudioBufferListPointer(p.assumingMemoryBound(to: AudioBufferList.self))
  var n = 0
  for b in list { n += Int(b.mNumberChannels) }
  return n
}
func rates(_ id: AudioDeviceID) -> [Double] {
  var a = addr(kAudioDevicePropertyAvailableNominalSampleRates); var size: UInt32 = 0
  guard AudioObjectGetPropertyDataSize(id, &a, 0, nil, &size) == noErr, size > 0 else { return [] }
  var rs = [AudioValueRange](repeating: AudioValueRange(mMinimum: 0, mMaximum: 0), count: Int(size) / MemoryLayout<AudioValueRange>.size)
  guard AudioObjectGetPropertyData(id, &a, 0, nil, &size, &rs) == noErr else { return [] }
  let common: [Double] = [44100, 48000, 88200, 96000, 176400, 192000, 352800, 384000, 705600, 768000]
  var found: [Double] = []
  for c in common {
    var ok = false
    for r in rs { if r.mMinimum <= c && c <= r.mMaximum { ok = true } }
    if ok { found.append(c) }
  }
  return found
}
func transport(_ id: AudioDeviceID) -> String {
  guard let t = u32(id, kAudioDevicePropertyTransportType) else { return "unknown" }
  if t == kAudioDeviceTransportTypeBuiltIn { return "builtin" }
  if t == kAudioDeviceTransportTypeUSB { return "usb" }
  if t == kAudioDeviceTransportTypeBluetooth || t == kAudioDeviceTransportTypeBluetoothLE { return "bluetooth" }
  if t == kAudioDeviceTransportTypeHDMI { return "hdmi" }
  if t == kAudioDeviceTransportTypeDisplayPort { return "displayport" }
  if t == kAudioDeviceTransportTypeThunderbolt { return "thunderbolt" }
  if t == kAudioDeviceTransportTypeFireWire { return "firewire" }
  if t == kAudioDeviceTransportTypeAirPlay { return "airplay" }
  if t == kAudioDeviceTransportTypeVirtual { return "virtual" }
  if t == kAudioDeviceTransportTypeAggregate { return "aggregate" }
  return "other"
}
// bit depth the device itself is set to (first output stream)
func bits(_ id: AudioDeviceID) -> Int {
  var a = addr(kAudioDevicePropertyStreams, kAudioDevicePropertyScopeOutput); var size: UInt32 = 0
  guard AudioObjectGetPropertyDataSize(id, &a, 0, nil, &size) == noErr, size > 0 else { return 0 }
  var ss = [AudioStreamID](repeating: 0, count: Int(size) / MemoryLayout<AudioStreamID>.size)
  guard AudioObjectGetPropertyData(id, &a, 0, nil, &size, &ss) == noErr, ss.count > 0 else { return 0 }
  var f = AudioStreamBasicDescription(); var fs = UInt32(MemoryLayout<AudioStreamBasicDescription>.size)
  var fa = addr(kAudioStreamPropertyPhysicalFormat)
  guard AudioObjectGetPropertyData(ss[0], &fa, 0, nil, &fs, &f) == noErr else { return 0 }
  return Int(f.mBitsPerChannel)
}
// process that holds the device for itself alone (-1 = nobody)
func hog(_ id: AudioDeviceID) -> Int {
  var a = addr(kAudioDevicePropertyHogMode); var v = Int32(-1); var size = UInt32(MemoryLayout<Int32>.size)
  guard AudioObjectHasProperty(id, &a), AudioObjectGetPropertyData(id, &a, 0, nil, &size, &v) == noErr else { return -1 }
  return Int(v)
}
func out(_ o: Any) {
  if let d = try? JSONSerialization.data(withJSONObject: o), let s = String(data: d, encoding: .utf8) { print(s) }
}

let args = CommandLine.arguments
let cmd = args.count > 1 ? args[1] : "list"
switch cmd {
case "list":
  let def = defaultOutput()
  var list: [[String: Any]] = []
  for id in devices() where isOutput(id) {
    var d: [String: Any] = ["uid": cfString(id, kAudioDevicePropertyDeviceUID), "name": cfString(id, kAudioObjectPropertyName), "default": id == def]
    if let v = getVol(id) { d["volume"] = v; d["hasVolume"] = true } else { d["hasVolume"] = false }
    list.append(d)
  }
  out(["devices": list])
case "info":
  let def = defaultOutput(); let defIn = defaultInput()
  var list: [[String: Any]] = []
  for id in devices() {
    let outCh = channels(id, kAudioDevicePropertyScopeOutput), inCh = channels(id, kAudioDevicePropertyScopeInput)
    var d: [String: Any] = ["uid": cfString(id, kAudioDevicePropertyDeviceUID), "name": cfString(id, kAudioObjectPropertyName), "maker": cfString(id, kAudioObjectPropertyManufacturer),
      "transport": transport(id), "out": outCh, "in": inCh, "rate": nominalRate(id), "rates": rates(id), "bits": bits(id), "hog": hog(id), "defaultOut": id == def, "defaultIn": id == defIn]
    if outCh > 0, let v = getVol(id) { d["volume"] = v; d["hasVolume"] = true } else { d["hasVolume"] = false }
    list.append(d)
  }
  out(["devices": list])
case "rate":
  guard args.count > 3, let id = byUID(args[2]), let hz = Double(args[3]) else { out(["error": "usage: rate <uid> <hz>"]); exit(1) }
  var ra = addr(kAudioDevicePropertyNominalSampleRate); var want = Float64(hz)
  let st = AudioObjectSetPropertyData(id, &ra, 0, nil, UInt32(MemoryLayout<Float64>.size), &want)
  var now = nominalRate(id); var n = 0
  while st == noErr && abs(now - hz) > 1 && n < 40 { usleep(50000); now = nominalRate(id); n += 1 }   // the device needs a moment to switch
  out(["ok": st == noErr && abs(now - hz) <= 1, "rate": now])
case "get":
  guard args.count > 2, let id = byUID(args[2]) else { out(["error": "no such device"]); exit(1) }
  if let v = getVol(id) { out(["uid": args[2], "volume": v]) } else { out(["uid": args[2], "error": "fixed volume"]) }
case "set":
  guard args.count > 3, let id = byUID(args[2]), let v = Float(args[3]) else { out(["error": "usage: set <uid> <0..1>"]); exit(1) }
  let ok = setVol(id, v); out(["ok": ok, "volume": getVol(id) ?? -1])
default:
  out(["error": "unknown command"]); exit(1)
}
