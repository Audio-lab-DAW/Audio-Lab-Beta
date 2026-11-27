"""Task NB-R4a, part 1: the device layer and the readers (review RN5 C7, C10). Anchors asserted once.
- coreaudio.h: dither off by default (16-bit material passes bit for bit); Watcher keeps the output stream it listens to
- coreaudio.cpp: the watcher also listens to the stream's virtual and physical format ("format" event), so the engine
  can restart its stream when another program or a re-plug changes the format (C7)
- nulldevice.cpp: the null device offers 16-bit and 24-bit integer formats as well as float; a stream on an integer,
  unmixable format writes the bytes through sample_convert.h and records what they decode to, like a DAC would get
  them; null change "format" (value 16, 24 or 32) changes the format from outside and posts "format"
- minijson.h: \\uXXXX (and surrogate pairs) become UTF-8, \\b \\f \\r \\/ read; device names with accents survive (C10)
- wav.h: the fmt chunk is read only when it is complete; a chunk length past the end stops the reader (C10)
"""
import os
R = os.path.join(os.path.dirname(__file__), "..", "..", "..")
def edit(rel, pairs):
    p = os.path.join(R, rel); s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:70]); s = s.replace(a, b)
    open(p, "w").write(s)

edit("native/common/coreaudio.h", [
 ("    WatchFn fn = nullptr; void* user = nullptr; uint32_t dev = 0; bool system = false;",
  "    WatchFn fn = nullptr; void* user = nullptr; uint32_t dev = 0, stream = 0; bool system = false;   // stream: its format is watched too (\"format\", task NB-R4)"),
 ("    bool dither16 = true; uint32_t ditherState = 0x1234abcdu;",
  "    bool dither16 = false; uint32_t ditherState = 0x1234abcdu;   // task NB-R4 (review C7): off, so 16-bit material reaches a 16-bit DAC bit for bit"),
])

edit("native/common/coreaudio.cpp", [
 ("            case kAudioDevicePropertyBufferFrameSize: what = \"buffer\"; break;",
  "            case kAudioDevicePropertyBufferFrameSize: what = \"buffer\"; break;\n            case kAudioStreamPropertyVirtualFormat: case kAudioStreamPropertyPhysicalFormat: what = \"format\"; break;   // task NB-R4 (C7)"),
 ("""void Watcher::watchDevice(uint32_t d) {
    std::vector<AudioObjectPropertyAddress> v; deviceWatchAddrs(v);
    if (dev) for (auto& a : v) if (AudioObjectHasProperty(dev, &a)) AudioObjectRemovePropertyListener(dev, &a, watchProc, this);
    dev = d;
    if (dev) for (auto& a : v) if (AudioObjectHasProperty(dev, &a)) AudioObjectAddPropertyListener(dev, &a, watchProc, this);
}""",
 """void Watcher::watchDevice(uint32_t d) {
    std::vector<AudioObjectPropertyAddress> v; deviceWatchAddrs(v);
    // task NB-R4 (review C7): the format lives on the device's first output stream, not on the device
    AudioObjectPropertyAddress sf[2] = { addr(kAudioStreamPropertyVirtualFormat), addr(kAudioStreamPropertyPhysicalFormat) };
    if (dev) for (auto& a : v) if (AudioObjectHasProperty(dev, &a)) AudioObjectRemovePropertyListener(dev, &a, watchProc, this);
    if (stream) for (auto& a : sf) if (AudioObjectHasProperty(stream, &a)) AudioObjectRemovePropertyListener(stream, &a, watchProc, this);
    dev = d; stream = 0;
    if (dev) for (auto& a : v) if (AudioObjectHasProperty(dev, &a)) AudioObjectAddPropertyListener(dev, &a, watchProc, this);
    if (dev) {
        auto sb = getBytes(dev, addr(kAudioDevicePropertyStreams, kAudioObjectPropertyScopeOutput));
        if (sb.size() >= sizeof(AudioStreamID)) stream = *(const AudioStreamID*)sb.data();
        if (stream) for (auto& a : sf) if (AudioObjectHasProperty(stream, &a)) AudioObjectAddPropertyListener(stream, &a, watchProc, this);
    }
}"""),
])

edit("native/common/nulldevice.cpp", [
 ("#include \"wav.h\"\n", "#include \"wav.h\"\n#include \"../engine/sample_convert.h\"\n"),
 ("    for (double r : d->rates) { v.push_back({ r, 32, 2, true, true }); v.push_back({ r, 24, 2, false, false }); }",
  "    for (double r : d->rates) { v.push_back({ r, 32, 2, true, true }); v.push_back({ r, 24, 2, false, false }); v.push_back({ r, 16, 2, false, false }); }"),
 ("    if (bits != 32 && bits != 24) { err = \"32-bit float or 24-bit integer\"; now = infoOf(*d).physicalFormat; return false; }",
  "    if (bits != 32 && bits != 24 && bits != 16) { err = \"32-bit float, 24-bit or 16-bit integer\"; now = infoOf(*d).physicalFormat; return false; }"),
 ("std::string virtualFormatText(uint32_t dev) { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); return d ? \"32-bit float, 2 ch, \" + jnum(d->rate) + \" Hz (null device)\" : \"\"; }",
  "// an integer format the system does not mix is handed to the program as it is (as Core Audio does); otherwise float\nstatic bool nullInt(const NullDev& d) { return !d.isFloat && !d.mixable; }\nstd::string virtualFormatText(uint32_t dev) { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(dev); if (!d) return \"\"; return (nullInt(*d) ? std::to_string(d->bits) + \"-bit integer\" : std::string(\"32-bit float\")) + \", 2 ch, \" + jnum(d->rate) + \" Hz (null device)\"; }"),
 ("""    vFloat = true; vBits = 32; vBytes = 4; formatText = virtualFormatText(device);""",
  """    { std::lock_guard<std::mutex> g(gLock); NullDev* d = find(device); bool in = d && nullInt(*d);
      vFloat = !in; vBits = in ? d->bits : 32; vBytes = in ? (d->bits == 16 ? 2 : 4) : 4; vAlignedHigh = true; vBigEndian = false; }
    formatText = virtualFormatText(device);"""),
 ("""            if (r->recording) { r->rec.sr = (int)rate; for (uint32_t i = 0; i < n; i++) { r->rec.data.push_back(L[i]); r->rec.data.push_back(R[i]); } }""",
  """            if (!self->vFloat) {   // task NB-R4: an integer format: the bytes are written as for the DAC, the recording is what they decode to
                SampleFormat sf; sf.isFloat = false; sf.bits = self->vBits; sf.bytes = self->vBytes; sf.alignedHigh = true;
                Dither dth; dth.s = self->ditherState; std::vector<uint8_t> by((size_t)n * sf.bytes * 2);
                for (int c = 0; c < 2; c++) writeChannel(out[c], (int)n, by.data() + c * sf.bytes, sf.bytes * 2, sf, (sf.bits <= 16 && self->dither16) ? &dth : nullptr);
                self->ditherState = dth.s;
                double sc = (double)((int64_t)1 << (sf.bits - 1));
                for (uint32_t i = 0; i < n; i++) for (int c = 0; c < 2; c++) {
                    uint32_t u = 0; const uint8_t* p = by.data() + ((size_t)i * 2 + c) * sf.bytes; for (int b = 0; b < sf.bytes; b++) u |= (uint32_t)p[b] << (8 * b);
                    int32_t s = (int32_t)u >> (sf.bytes * 8 - sf.bits);   // aligned high: the sign comes down with the value
                    out[c][i] = (float)((double)s / sc);
                }
            }
            if (r->recording) { r->rec.sr = (int)rate; for (uint32_t i = 0; i < n; i++) { r->rec.data.push_back(L[i]); r->rec.data.push_back(R[i]); } }"""),
 ("""      else if (what == "hog") { d->hogPid = (int)value; ev = "exclusive"; }""",
  """      else if (what == "hog") { d->hogPid = (int)value; ev = "exclusive"; }
      // task NB-R4: another program changes the device's format (32 float and mixable, or 24 or 16 integer and not mixable)
      else if (what == "format") { int b = (int)value; if (b != 32 && b != 24 && b != 16) return "32, 24 or 16"; d->bits = b; d->isFloat = b == 32; d->mixable = b == 32; ev = "format"; }"""),
])

edit("native/engine/minijson.h", [
 ("""            if (s[i] == '\\\\' && i + 1 < n) { i++; char c = s[i]; out += c == 'n' ? '\\n' : c == 't' ? '\\t' : c; }""",
  """            if (s[i] == '\\\\' && i + 1 < n) {
                i++; char c = s[i];
                if (c == 'u') {   // task NB-R4 (review C10): \\uXXXX to UTF-8, surrogate pairs joined
                    auto hex4 = [&](size_t at, uint32_t& v) { if (at + 4 > n) return false; v = 0; for (size_t k = at; k < at + 4; k++) { char h = s[k]; v <<= 4; if (h >= '0' && h <= '9') v |= (uint32_t)(h - '0'); else if (h >= 'a' && h <= 'f') v |= (uint32_t)(h - 'a' + 10); else if (h >= 'A' && h <= 'F') v |= (uint32_t)(h - 'A' + 10); else return false; } return true; };
                    uint32_t cp; if (!hex4(i + 1, cp)) return false; i += 4;
                    if (cp >= 0xD800 && cp < 0xDC00) { uint32_t lo; if (i + 2 < n && s[i + 1] == '\\\\' && s[i + 2] == 'u' && hex4(i + 3, lo) && lo >= 0xDC00 && lo < 0xE000) { cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00); i += 6; } else cp = 0xFFFD; }
                    else if (cp >= 0xDC00 && cp < 0xE000) cp = 0xFFFD;
                    if (cp < 0x80) out += (char)cp;
                    else if (cp < 0x800) { out += (char)(0xC0 | (cp >> 6)); out += (char)(0x80 | (cp & 0x3F)); }
                    else if (cp < 0x10000) { out += (char)(0xE0 | (cp >> 12)); out += (char)(0x80 | ((cp >> 6) & 0x3F)); out += (char)(0x80 | (cp & 0x3F)); }
                    else { out += (char)(0xF0 | (cp >> 18)); out += (char)(0x80 | ((cp >> 12) & 0x3F)); out += (char)(0x80 | ((cp >> 6) & 0x3F)); out += (char)(0x80 | (cp & 0x3F)); }
                }
                else out += c == 'n' ? '\\n' : c == 't' ? '\\t' : c == 'r' ? '\\r' : c == 'b' ? '\\b' : c == 'f' ? '\\f' : c;
            }"""),
 ("#include <cstdlib>\n", "#include <cstdint>\n#include <cstdlib>\n"),
])

edit("native/common/wav.h", [
 ("""        uint32_t len; memcpy(&len, &b[p + 4], 4);
        if (!memcmp(&b[p], "fmt ", 4)) {""",
  """        uint32_t len; memcpy(&len, &b[p + 4], 4);
        if ((size_t)len > b.size() - p - 8 && memcmp(&b[p], "data", 4)) break;   // task NB-R4 (review C10): a chunk that runs past the end
        if (!memcmp(&b[p], "fmt ", 4)) {
            if (len < 16) { err = "the WAV file's format chunk is too short"; return false; }"""),
])
print("nb_r4_common: ok")
