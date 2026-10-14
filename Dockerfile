FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-minimal \
        openssh-server \
        ca-certificates curl \
        libjson-c5 libwebsockets17 libuv1 libwebsockets-evlib-uv \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz \
        | tar xz -C /usr/local/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake git libjson-c-dev libwebsockets-dev libuv1-dev \
    && git clone --depth 1 https://github.com/tsl0922/ttyd.git /tmp/ttyd \
    && cd /tmp/ttyd && mkdir build && cd build \
    && cmake .. && make -j"$(nproc)" && make install \
    && apt-get purge -y build-essential cmake git libjson-c-dev libwebsockets-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /tmp/ttyd

RUN mkdir -p /var/run/sshd /root/.ssh \
    && echo "PermitRootLogin yes" >> /etc/ssh/sshd_config \
    && echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config \
    && echo "PermitEmptyPasswords no" >> /etc/ssh/sshd_config \
    && echo "ClientAliveInterval 30" >> /etc/ssh/sshd_config \
    && echo "ClientAliveCountMax 6" >> /etc/ssh/sshd_config \
    && usermod -s /bin/bash root \
    && echo "DEATH shell ready" > /etc/motd

WORKDIR /app
COPY officialv3.py /app/officialv3.py
COPY entry.sh /app/entry.sh
RUN sed -i 's/\r$//' /app/entry.sh && chmod +x /app/entry.sh

RUN mkdir -p /data
ENV DEATH_DATA_DIR=/data

EXPOSE 8080
CMD ["/app/entry.sh"]
