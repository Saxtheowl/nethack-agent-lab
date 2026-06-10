FROM debian:12

ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server tmux python3 python3-pip python3-pexpect \
    libncurses6 locales procps \
    && sed -i 's/# en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash nethack && passwd -d nethack

COPY opt/games /opt/nethack/games
COPY opt/nethackdir /opt/nethack/nethackdir
COPY config/sshd_config /etc/ssh/sshd_config
COPY config/nethackrc.bot /opt/nethack/nethackrc.bot
COPY config/nethackrc.player /opt/nethack/nethackrc.player
COPY scripts/entrypoint.sh /opt/nethack/entrypoint.sh
COPY scripts/menu.sh /opt/nethack/menu.sh
COPY bot/ /opt/nethack/bot/

RUN mkdir -p /data/sessions /data/saves /data/claimed_wishes /run/sshd \
    && ln -sf /opt/nethack/games/nethack /usr/local/bin/nethack \
    && chmod +x /opt/nethack/entrypoint.sh /opt/nethack/menu.sh /opt/nethack/bot/*.py \
    && chmod -R 775 /opt/nethack/nethackdir \
    && chmod 2775 /opt/nethack/nethackdir/save 2>/dev/null || true \
    && chown -R nethack:nethack /opt/nethack /data

EXPOSE 22

ENTRYPOINT ["/opt/nethack/entrypoint.sh"]
