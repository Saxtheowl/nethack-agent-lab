FROM eclipse-temurin:8-jdk-jammy

ENV DEBIAN_FRONTEND=noninteractive
ENV NH343_PREFIX=/opt/nh343
ENV BOT_HOME=/opt/bothack
ENV LAB_HOME=/lab
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV ANT_OPTS=-Dfile.encoding=UTF-8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ant \
        bsdextrautils \
        build-essential \
        ca-certificates \
        curl \
        flex \
        bison \
        git \
        groff \
        leiningen \
        libfaketime \
        libjsch-java \
        libncurses-dev \
        maven \
        openssh-server \
        procps \
        python3 \
        python3-pip \
        python3-venv \
        ttyrec \
        wget \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash botlab \
    && mkdir -p /run/sshd "$LAB_HOME" "$NH343_PREFIX" \
    && chown -R botlab:botlab "$LAB_HOME"

RUN set -eux; \
    git clone https://www.alt.org/nethack/nh343-nao.git /tmp/nh343-build; \
    cd /tmp/nh343-build; \
    sed -i 's|^PREFIX[[:space:]]*=.*|PREFIX = /opt/nh343|' Makefile; \
    sed -i 's|^CFLAGS =|CFLAGS = -fcommon |' src/Makefile; \
    sed -i 's|^WINTTYLIB =.*|WINTTYLIB = -lncurses|' src/Makefile; \
    sed -i 's|extern char \*tparm();|/* tparm declared by ncurses */|' win/tty/termcap.c; \
    perl -0pi -e 's|void\nsetrandom\\(\\)\n\\{\n\\s*|void\nsetrandom()\n{\n  {\n    const char *seed_env = getenv("NETHACK_SEED");\n    if (seed_env && *seed_env) {\n      srandom((unsigned int) strtoul(seed_env, (char **)0, 10));\n      return;\n    }\n  }\n\n|s' src/hacklib.c; \
    make all; \
    make install; \
    chmod -R a+rwX /opt/nh343/nh343; \
    chmod 0755 /opt/nh343/nh343/nethack.343-nao; \
    ln -sfn /opt/nh343/nh343 /nh343; \
    rm -rf /tmp/nh343-build

RUN git clone --depth 1 https://github.com/krajj7/BotHack.git "$BOT_HOME" \
    && cd "$BOT_HOME" \
    && sed -i 's|\[org.clojars.achim/multiset "0.1.0-SNAPSHOT"\]|[metametadata/multiset "0.1.1"]|' project.clj \
    && python3 -c 'from pathlib import Path; p=Path("jta26/jni/src/HandlerPTY.c"); s=p.read_text(); s=s.replace("#include <pty.h>\t\t/* most interesting part: openpty, forkpty */", "#include <pty.h>\t\t/* most interesting part: openpty, forkpty */\n\nextern char **environ;"); s=s.replace("\t\tchar *eenvp[] = { \"TERM=xterm\", NULL };\n\t\texecve(ncmd, eargv, eenvp);", "\t\texecve(ncmd, eargv, environ);"); p.write_text(s)' \
    && CLASSPATH=/usr/share/java/jsch.jar ant -f jta26/build.xml \
    && cd jta26/jni/linux \
    && javac -h . -classpath ../.. ../../de/mud/jta/plugin/HandlerPTY.java \
    && cp de_mud_jta_plugin_HandlerPTY.h HandlerPTY.h \
    && gcc -Ofast -fPIC -c -Wall -I. -I"$JAVA_HOME/include" -I"$JAVA_HOME/include/linux" -o HandlerPTY.lo ../src/HandlerPTY.c \
    && gcc -shared -lutil -o libjtapty.so HandlerPTY.lo \
    && mkdir -p "$LAB_HOME"/{recordings,wins,seeds,logs,workspace}

COPY replay_app /opt/replay_app
COPY tests /opt/tests
COPY scripts /opt/botlab_scripts
RUN chmod +x /opt/botlab_scripts/*.sh \
    && python3 -m pip install --no-cache-dir pyte pytest

COPY docker/shell-config.edn /opt/bothack/config/lab-shell-config.edn
COPY docker/nethackrc /home/botlab/.nethackrc
RUN chown -R botlab:botlab /home/botlab "$LAB_HOME" "$BOT_HOME"
RUN su botlab -c 'cd /opt/bothack && JAVA_HOME=/opt/java/openjdk PATH=/opt/java/openjdk/bin:$PATH lein compile'

EXPOSE 22 8080

CMD ["/opt/botlab_scripts/entrypoint.sh"]
