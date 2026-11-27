#!/bin/sh
# Task NL7: builds and runs live_tools_test.cpp normally, with ASan+UBSan, and with TSan. Usage: run.sh [outdir]
set -e
D=$(cd "$(dirname "$0")" && pwd); O=${1:-/tmp/nl7-tools}; mkdir -p "$O"
CXX=${CXX:-c++}
$CXX -std=c++17 -O2 -pthread "$D/live_tools_test.cpp" -o "$O/t_plain" && "$O/t_plain"
$CXX -std=c++17 -O1 -g -pthread -fsanitize=address,undefined -fno-sanitize-recover=all "$D/live_tools_test.cpp" -o "$O/t_asan" && "$O/t_asan" | tail -1
$CXX -std=c++17 -O1 -g -pthread -fsanitize=thread "$D/live_tools_test.cpp" -o "$O/t_tsan" && "$O/t_tsan" | tail -1
