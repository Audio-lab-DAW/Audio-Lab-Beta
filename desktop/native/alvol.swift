// alvol: tiny Core Audio helper for AudioLab Studio (macOS).
//   alvol list              -> JSON: default output uid + output devices with hardware-volume info
//   alvol get <uid>         -> JSON: {"uid":..,"volume":0..1}
//   alvol set <uid> <0..1>  -> JSON: {"ok":true,"volume":..}
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
case "get":
  guard args.count > 2, let id = byUID(args[2]) else { out(["error": "no such device"]); exit(1) }
  if let v = getVol(id) { out(["uid": args[2], "volume": v]) } else { out(["uid": args[2], "error": "fixed volume"]) }
case "set":
  guard args.count > 3, let id = byUID(args[2]), let v = Float(args[3]) else { out(["error": "usage: set <uid> <0..1>"]); exit(1) }
  let ok = setVol(id, v); out(["ok": ok, "volume": getVol(id) ?? -1])
default:
  out(["error": "unknown command"]); exit(1)
}
