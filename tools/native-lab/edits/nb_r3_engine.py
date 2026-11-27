"""Task NB-R3: a source switch no longer waits for a sender that has stopped (a frozen feeder kept the engine's
command thread in stopSocket's join until the sender died). The socket thread's client is shut down from
stopSocket under a small lock (command and socket threads only, never the audio thread). alengine 0.4.
Each anchor is asserted to occur exactly once."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else "native/engine/engine_main.cpp"
s = open(p).read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
rep("std::atomic<bool> sockClient{false};",
    "std::atomic<bool> sockClient{false};\n    std::mutex clientLock; int clientFd = -1;   // task NB-R3: the connected sender, so stopSocket can end a read that would never return")
rep("""    E.sockRun = false;
    if (E.listenFd >= 0) { shutdown(E.listenFd, SHUT_RDWR); close(E.listenFd); E.listenFd = -1; }""",
"""    E.sockRun = false;
    if (E.listenFd >= 0) { shutdown(E.listenFd, SHUT_RDWR); close(E.listenFd); E.listenFd = -1; }
    // a sender that stopped sending (frozen, hung) would keep the socket thread in read() and this join waiting
    { std::lock_guard<std::mutex> g(E.clientLock); if (E.clientFd >= 0) shutdown(E.clientFd, SHUT_RDWR); }""")
rep("""            if (c < 0) break;
            E.sockClient = true; carry = 0;""",
"""            if (c < 0) break;
            { std::lock_guard<std::mutex> g(E.clientLock); if (!E.sockRun.load()) { close(c); break; } E.clientFd = c; }
            E.sockClient = true; carry = 0;""")
rep("""            close(c); E.sockClient = false;""",
"""            { std::lock_guard<std::mutex> g(E.clientLock); E.clientFd = -1; close(c); }
            E.sockClient = false;""")
rep('\\"engine\\":\\"alengine 0.3\\"', '\\"engine\\":\\"alengine 0.4\\"')
open(p, "w").write(s)
print("nb_r3_engine: ok")
