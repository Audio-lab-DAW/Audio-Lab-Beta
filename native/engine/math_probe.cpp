// almathprobe: the engine's maths functions against the browser's (task NB-N3c). Input from
// tools/native-lab/math_probe.py: 400,000 records of 8 doubles (a, sin a, cos a, d, 10^(d/20), exp(-d/7), l, log10 l).
#include <cmath>
#include <cstdio>
#include <vector>
#include "core/jsmath.h"
int main(int argc, char** argv) {
    if (argc < 2) { fprintf(stderr, "usage: almathprobe math_vals.bin\n"); return 2; }
    FILE* f = fopen(argv[1], "rb"); if (!f) return 2;
    std::vector<double> v; double buf[8];
    while (fread(buf, 8, 8, f) == 8) v.insert(v.end(), buf, buf + 8);
    fclose(f);
    const size_t n = v.size() / 8;
    long e[5] = {0}, s[5] = {0};
    for (size_t i = 0; i < n; i++) {
        const double* r = &v[8 * i];
        if (al::js::sin(r[0]) != r[1]) e[0]++;
        if (al::js::cos(r[0]) != r[2]) e[1]++;
        if (al::js::pow(10.0, r[3] / 20) != r[4]) e[2]++;
        if (al::js::exp(-r[3] / 7) != r[5]) e[3]++;
        if (al::js::log10(r[6]) != r[7]) e[4]++;
        if (std::sin(r[0]) != r[1]) s[0]++;
        if (std::cos(r[0]) != r[2]) s[1]++;
        if (std::pow(10.0, r[3] / 20) != r[4]) s[2]++;
        if (std::exp(-r[3] / 7) != r[5]) s[3]++;
        if (std::log10(r[6]) != r[7]) s[4]++;
    }
    printf("{\"args\":%zu,\"engine\":{\"sin\":%ld,\"cos\":%ld,\"pow\":%ld,\"exp\":%ld,\"log10\":%ld},"
           "\"system\":{\"sin\":%ld,\"cos\":%ld,\"pow\":%ld,\"exp\":%ld,\"log10\":%ld}}\n",
           n, e[0], e[1], e[2], e[3], e[4], s[0], s[1], s[2], s[3], s[4]);
    return (e[0] || e[1] || e[2] || e[3] || e[4]) ? 1 : 0;
}
