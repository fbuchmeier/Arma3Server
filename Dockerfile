FROM debian:bullseye-slim

LABEL maintainer="Florian - github.com/fbuchmeier"
LABEL org.opencontainers.image.source=https://github.com/fbuchmeier/arma3server

RUN groupadd -r steam -g 433 && \
    useradd -u 431 -r -g steam -s /sbin/nologin -c "Docker image user" steam

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update \
    && apt-get install -y --no-install-recommends --no-install-suggests \
        python3 \
        python3-pip \
        lib32stdc++6 \
        lib32gcc-s1 \
        libcurl4 \
        wget \
        ca-certificates \
        rsync \
    && apt-get remove --purge -y \
    && apt-get clean autoclean \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/steamcmd \
    && mkdir /arma3 \
    && wget -qO- 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz' | tar zxf - -C /opt/steamcmd \
    && chown -R steam:steam /opt/steamcmd \
    && chown -R steam:steam /arma3 \
    && mkdir /steamcmd \
    && chown steam:steam /steamcmd

ENV ARMA_BINARY=/arma3/arma3server
ENV ARMA_CONFIG=main.cfg
ENV ARMA_PARAMS=
ENV ARMA_PROFILE=main
ENV ARMA_WORLD=empty
ENV ARMA_LIMITFPS=100
ENV ARMA_CDLC=
ENV HEADLESS_CLIENTS=0
ENV HEADLESS_CLIENTS_PROFILE="\$profile-hc-\$i"
ENV PORT=2302
ENV STEAM_BRANCH=public
ENV STEAM_BRANCH_PASSWORD=
ENV MODS_LOCAL=true
ENV MODS_PRESET=
ENV SKIP_INSTALL=false

EXPOSE 2302/udp
EXPOSE 2303/udp
EXPOSE 2304/udp
EXPOSE 2305/udp
EXPOSE 2306/udp
EXPOSE 8000/tcp

WORKDIR /arma3

VOLUME /steamcmd
VOLUME /home/steam

STOPSIGNAL SIGINT

COPY *.py /
COPY entrypoint.sh /entrypoint.sh
COPY requirements.txt /requirements.txt

RUN pip3 install -r /requirements.txt

USER steam

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python3","/launch.py"]
