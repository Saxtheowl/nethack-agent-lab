"""Drive the Clojure oracle: feed cases, collect EDN results.

Usage: run_clojure_oracle(cases) -> list of parsed results
  cases is a list of (op, [arg-edn-strings...]) tuples.
"""

import subprocess
import os

from . import edn

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def oracle_command():
    jdk8 = os.environ.get("JDK8_HOME",
                          os.path.join(ROOT, ".local", "jdk8"))
    java = os.path.join(jdk8, "bin", "java")
    lein_dir = os.path.join(ROOT, "tools")
    log4j = os.path.join(ROOT, "tools", "log4j-quiet.properties")
    src = os.path.join(ROOT, "upstream", "BotHack")
    return (src, java, lein_dir, log4j)


def run(cases, timeout=600):
    src, java, lein_dir, log4j = oracle_command()
    env = dict(os.environ)
    env["JAVA_HOME"] = os.environ.get("JDK8_HOME",
                                      os.path.join(ROOT, ".local", "jdk8"))
    env["PATH"] = env["JAVA_HOME"] + "/bin:" + lein_dir + ":" + env.get("PATH", "")
    env["JVM_OPTS"] = "-Xmx1g -Dlog4j.configuration=file:%s" % log4j

    stdin = "".join("\t".join([op] + list(args)) + "\n" for op, args in cases)

    cmd = ["lein", "update-in", ":source-paths", "conj",
           '"%s/tools"' % ROOT, "--", "run", "-m", "cljcmp.oracle"]
    proc = subprocess.run(cmd, cwd=src, env=env, input=stdin,
                          capture_output=True, text=True, timeout=timeout)
    out = parse_output(proc.stdout)
    return out, proc


def parse_output(stdout):
    results = []
    for line in stdout.splitlines():
        if line.startswith("RESULT:"):
            results.append(edn.loads(line[len("RESULT:"):]))
    return results