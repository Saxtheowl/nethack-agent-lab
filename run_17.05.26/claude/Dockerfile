# syntax=docker/dockerfile:1.4
# =============================================================================
# Super-NetHack: BotHack on NetHack 3.4.3 (NAO patchset)
# Records 10 winning games (seed + ttyrec) and serves a web replay UI.
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build NetHack 3.4.3 (NAO) with deterministic seed patch
# -----------------------------------------------------------------------------
FROM debian:bookworm-slim AS nh-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libncurses-dev bison flex groff git ca-certificates \
      patch gzip \
    && rm -rf /var/lib/apt/lists/*

# NAO repo = NetHack 3.4.3 with the alt.org patches already applied
RUN git clone https://www.alt.org/nethack/nh343-nao.git /src && \
    cd /src && git checkout master

WORKDIR /src

# Our seed-env patch — adds NETHACK_SEED support to init_random()
COPY patches/01-seed-env.patch /tmp/01-seed-env.patch
RUN patch -p1 < /tmp/01-seed-env.patch

# NAO sources already have HACKDIR=/nh343. Set PREFIX="" so install lands there.
RUN sed -i 's|^PREFIX\s*=.*|PREFIX =|' sys/unix/Makefile.top && \
    sed -i 's|^GAMEUID\s*=.*|GAMEUID = root|' sys/unix/Makefile.top && \
    sed -i 's|^GAMEGRP\s*=.*|GAMEGRP = root|' sys/unix/Makefile.top

# Add -fcommon for modern gcc (3.4.3 has many tentative definitions)
RUN sed -i 's|^CFLAGS\s*=.*|CFLAGS = -g -O2 -fcommon -I../include|' sys/unix/Makefile.src

# The NAO repo already has the Makefile symlinks committed at the project root,
# so we skip sys/unix/setup.sh and go straight to make.
RUN make -j"$(nproc)" 2>&1 | tail -100
RUN make install 2>&1 | tail -50
# Make data files world-readable, /nh343/var world-writable (multiple games share it)
RUN chmod -R a+rX /nh343 && chmod a+rwx /nh343/var /nh343/var/save 2>/dev/null || true

# -----------------------------------------------------------------------------
# Stage 2: Build BotHack (Clojure + Java + jta26/JNI)
# Uses JDK 8 because BotHack pulls multiset 0.1.0-SNAPSHOT which fails to
# compile on JDK 9+ (toArray overload ambiguity in deftype-implemented
# Collection). JDK 8 keeps Clojure 1.6 happy.
# -----------------------------------------------------------------------------
FROM eclipse-temurin:8-jdk AS bothack-builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      make build-essential \
      git ca-certificates curl wget \
    && rm -rf /var/lib/apt/lists/*

# Install Leiningen
RUN curl -fsSL https://raw.githubusercontent.com/technomancy/leiningen/stable/bin/lein \
      -o /usr/local/bin/lein && chmod +x /usr/local/bin/lein
ENV LEIN_ROOT=1
RUN lein version

WORKDIR /build
RUN git clone https://github.com/krajj7/BotHack.git /build/BotHack
WORKDIR /build/BotHack

# Patch the JNI shell handler so it INHERITS our process env when execve'ing
# NetHack. Upstream hard-codes the child env to { TERM=xterm } only, which
# silently drops NETHACK_SEED, WORKER_ID, NETHACKDIR, HOME, NETHACKOPTIONS …
COPY patches/02-handlerpty-env.patch /tmp/02-handlerpty-env.patch
RUN patch -p1 < /tmp/02-handlerpty-env.patch

# Route the "In what direction do you want to dig?" prompt to the public
# DirectionHandler instead of throwing IllegalStateException. Without this,
# the bot stalls on its core descend-by-digging strategy and never reaches
# the late game — observed 0/297 ascensions before this fix.
COPY patches/03-scraper-dig-direction.patch /tmp/03-scraper-dig-direction.patch
RUN patch -p1 < /tmp/03-scraper-dig-direction.patch

# Keep -target/-source at 1.7 — eclipse-temurin:8-jdk accepts it natively.
# (Bumping it for newer JDKs broke the build because target 1.7 is no longer
# supported in JDK 12+.)

# Compile Clojure + Java sources via lein (this also compiles jta26/de/mud
# Java sources because they're listed in project.clj's :java-source-paths,
# AND lein puts jsch.jar on the classpath — which the bare `ant` build doesn't).
# We skip the upstream `ant` step entirely: it only produced .class files in
# the source tree for the JNI build to depend on, and we generate the JNI
# header explicitly with `javac -h` below.
RUN lein deps && lein compile

# Build the JNI native library for the local shell interface.
# Quirks fixed here:
#   • upstream Makefile uses `javah` (gone in JDK 10+) → we pre-generate
#     HandlerPTY.h with `javac -h` so make's `javah` rule never runs.
#   • Makefile's JNI_INCLUDE points at /usr/lib/j2sdk1.3/include → override.
WORKDIR /build/BotHack/jta26/jni/linux
RUN set -eux; \
    JAVA_HOME="${JAVA_HOME:-$(dirname $(dirname $(readlink -f $(which javac))))}"; \
    echo "JAVA_HOME=$JAVA_HOME"; \
    mkdir -p /tmp/jcompile; \
    javac -d /tmp/jcompile -h . \
          /build/BotHack/jta26/de/mud/jta/plugin/HandlerPTY.java; \
    cp -v de_mud_jta_plugin_HandlerPTY.h HandlerPTY.h; \
    # Also drop the .class file where the Makefile's dep would look for it,
    # so make's HandlerPTY.h target stays not-out-of-date.
    mkdir -p /build/BotHack/jta26/de/mud/jta/plugin; \
    cp /tmp/jcompile/de/mud/jta/plugin/HandlerPTY.class \
       /build/BotHack/jta26/de/mud/jta/plugin/HandlerPTY.class || true; \
    sed -i "s|^JNI_INCLUDE.*|JNI_INCLUDE = -I$JAVA_HOME/include -I$JAVA_HOME/include/linux|" Makefile; \
    sed -i 's|gcc -Ofast|gcc -O2|' Makefile; \
    make libjtapty.so; \
    ls -l libjtapty.so

# Produce an uberjar so we can run BotHack without lein at runtime (faster startup, no net)
WORKDIR /build/BotHack
RUN lein uberjar

# -----------------------------------------------------------------------------
# Stage 3: Runtime
# JRE 8 matches the build-time JDK 8 — keeps Clojure 1.6 reflection happy.
# -----------------------------------------------------------------------------
FROM eclipse-temurin:8-jre

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv \
      ttyrec ncurses-bin libncurses6 \
      openssh-server tmux locales procps less vim-tiny \
      ca-certificates curl patch \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i 's/# en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen && locale-gen

# Python deps for replay server
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir \
       fastapi==0.115.0 uvicorn[standard]==0.30.6 \
       pyte==0.8.2 jinja2==3.1.4

# Copy NetHack from builder
COPY --from=nh-builder /nh343 /nh343
# Make /nh343/var entries writable by the bot user (no setgid games trickery).
RUN chmod 777 /nh343/var && mkdir -p /nh343/var/save && chmod 777 /nh343/var/save \
    && touch /nh343/var/record /nh343/var/logfile /nh343/var/xlogfile \
             /nh343/var/livelog /nh343/var/perm \
    && chmod 666 /nh343/var/record /nh343/var/logfile /nh343/var/xlogfile \
             /nh343/var/livelog /nh343/var/perm

# Provision per-worker NetHack playgrounds for parallel games.
# Each /nh343-wN holds symlinks to the read-only data files of /nh343 plus its
# OWN writable perm/record/logfile/save/. At runtime, the launcher sets
# NETHACKDIR=/nh343-wN so NetHack chdirs there and uses local prefixes — no
# fcntl-lock contention on /nh343/var/perm between concurrent games.
RUN for i in 1 2 3 4 5 6 7 8; do \
      mkdir -p /nh343-w$i/save; \
      for f in /nh343/*; do \
        name=$(basename "$f"); \
        [ "$name" = "var" ] && continue; \
        ln -sf "$f" "/nh343-w$i/$name"; \
      done; \
      touch /nh343-w$i/perm /nh343-w$i/record /nh343-w$i/logfile \
            /nh343-w$i/xlogfile /nh343-w$i/livelog; \
      chmod 666 /nh343-w$i/perm /nh343-w$i/record /nh343-w$i/logfile \
                /nh343-w$i/xlogfile /nh343-w$i/livelog; \
      chmod 777 /nh343-w$i /nh343-w$i/save; \
    done

# Copy BotHack from builder
COPY --from=bothack-builder /build/BotHack /opt/bothack

# SSH setup
RUN useradd -m -s /bin/bash bot && passwd -d bot \
    && mkdir -p /var/run/sshd /data/games /data/logs \
    && chown -R bot:bot /data \
    && chown -R bot:bot /opt/bothack

# Symlinks for convenience
RUN ln -s /nh343/nethack.343-nao /usr/local/bin/nethack343

# Bothack nethackrc + configs
COPY config/nethackrc.bot /opt/bothack/bothack.nethackrc
COPY config/shell-config.edn /opt/bothack/config/shell-config.edn
COPY config/sshd_config /etc/ssh/sshd_config

# Runner + replay code
COPY runner/ /opt/runner/
COPY replay/ /opt/replay/
COPY scripts/entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh /opt/runner/*.sh /opt/runner/*.py 2>/dev/null || true \
    && chmod +x /opt/replay/*.py 2>/dev/null || true

EXPOSE 22 8080

ENTRYPOINT ["/opt/entrypoint.sh"]
