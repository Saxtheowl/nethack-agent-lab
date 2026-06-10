FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libncurses-dev curl ca-certificates git python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /lab

# NetHack 3.7 source (officiel, branche NetHack-3.7)
COPY third_party/nethack-3.7 /lab/third_party/nethack-3.7
RUN cd third_party/nethack-3.7 \
    && sys/unix/setup.sh sys/unix/hints/linux-minimal \
    && make fetch-lua \
    && make -j"$(nproc)" PREFIX=/lab/nh370 \
    && make install PREFIX=/lab/nh370 \
    && cp sys/unix/sysconf /lab/nh370/games/lib/nethackdir/sysconf \
    && sed -i 's/^WIZARDS=.*/WIZARDS=*/' /lab/nh370/games/lib/nethackdir/sysconf

RUN python3 -m venv /lab/venv && /lab/venv/bin/pip install --no-cache-dir pyte

COPY bot /lab/bot
COPY runner /lab/runner
COPY config /lab/config

ENV PYTHONUNBUFFERED=1
# usage: docker run image /lab/venv/bin/python /lab/runner/run_batch.py /data/batch -n 100 -j 16
CMD ["/lab/venv/bin/python", "/lab/runner/run_batch.py", "/data/batch", "-n", "10", "-j", "4"]
