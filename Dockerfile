# --- STAGE 1: Builder ---
FROM ardupilot/ardupilot-dev-base AS builder

ARG COPTER_TAG=Copter-4.5.7
ARG VEHICLE_TYPE=copter

RUN git clone --depth 1 --branch ${COPTER_TAG} --recurse-submodules https://github.com/ArduPilot/ardupilot.git /ardupilot
WORKDIR /ardupilot

# Build and STRIP binary
RUN ./waf configure --board sitl && ./waf ${VEHICLE_TYPE}
RUN strip /ardupilot/build/sitl/bin/arducopter

# --- STAGE 2: Final Image ---
FROM python:3.11-slim-bookworm

# Install ONLY runtime dependencies
RUN apt-get update && apt-get install -y \
    libxml2-dev libxslt-dev zlib1g-dev procps \
    && rm -rf /var/lib/apt/lists/*

# Install MAVProxy
RUN pip3 install --no-cache-dir pymavlink MAVProxy future pexpect

WORKDIR /ardupilot

# 1. Create structure
RUN mkdir -p /ardupilot/ArduCopter /ardupilot/build/sitl/bin /ardupilot/Tools/autotest

# 2. Copy the stripped binary
COPY --from=builder /ardupilot/build/sitl/bin/arducopter /ardupilot/build/sitl/bin/

# 3. Copy ALL scripts from autotest root
COPY --from=builder /ardupilot/Tools/autotest/*.py /ardupilot/Tools/autotest/
COPY --from=builder /ardupilot/Tools/autotest/*.sh /ardupilot/Tools/autotest/

# 4. Copy essential subdirectories for simulation logic
COPY --from=builder /ardupilot/Tools/autotest/pysim/ /ardupilot/Tools/autotest/pysim/
COPY --from=builder /ardupilot/Tools/autotest/default_params/ /ardupilot/Tools/autotest/default_params/

# 5. Copy Vehicle folder
COPY --from=builder /ardupilot/ArduCopter/ /ardupilot/ArduCopter/

# 6. Flag for sim_vehicle
RUN touch /ardupilot/WAF_FINISHED

# ENV variables
ENV INSTANCE=0 \
    LAT=-27.4831 \
    LON=-58.9328 \
    ALT=50 \
    DIR=0 \
    SPEEDUP=1 \
    VEHICLE=ArduCopter \
    MODEL=quad \
    OUT_ADDR=host.docker.internal:14550

EXPOSE 14550/udp
EXPOSE 5760/tcp

CMD python3 /ardupilot/Tools/autotest/sim_vehicle.py \
    --vehicle ${VEHICLE} \
    --frame ${MODEL} \
    -I${INSTANCE} \
    --custom-location=${LAT},${LON},${ALT},${DIR} \
    --speedup ${SPEEDUP} \
    --no-rebuild \
    --out=udp:${OUT_ADDR}