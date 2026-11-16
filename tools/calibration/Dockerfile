# Kalibr (ROS 1 Noetic) for AgriSense-360 camera calibration.
#
# Build context: third_party/sources/kalibr, pinned to upstream commit
# 1f60227442d25e36365ef5f72cd80b9666d73467 (see dependencies.repos).
#
# This image exists because Kalibr has no ROS 2 port and must not be installed
# into the Humble host. See docs/01_project_baseline.md section 6.

# Base image resolved on 2026-11-16:
# docker.io/osrf/ros@sha256:7dbfb9576d8e6d226c31e06129a82aaab8702695f38eca2116918cb9b9308797
FROM osrf/ros:noetic-desktop-full

ARG BUILD_JOBS=4

RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        git wget autoconf automake nano \
        python3-dev python3-pip python3-scipy python3-matplotlib \
        ipython3 python3-wxgtk4.0 python3-tk python3-igraph python3-pyx \
        libeigen3-dev libboost-all-dev libsuitesparse-dev \
        doxygen libopencv-dev \
        libpoco-dev libtbb-dev libblas-dev liblapack-dev libv4l-dev \
        python3-catkin-tools python3-osrf-pycommon \
    && rm -rf /var/lib/apt/lists/*

ENV WORKSPACE=/catkin_ws

RUN mkdir -p "${WORKSPACE}/src" \
    && cd "${WORKSPACE}" \
    && catkin init \
    && catkin config --extend /opt/ros/noetic \
    && catkin config --cmake-args -DCMAKE_BUILD_TYPE=Release

ADD . "${WORKSPACE}/src/kalibr"

RUN cd "${WORKSPACE}" && catkin build -j"${BUILD_JOBS}"

# kalibr_create_target_pdf draws its axis labels through pyx's TeX text engine.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        texlive-latex-base texlive-fonts-recommended texlive-font-utils \
    && rm -rf /var/lib/apt/lists/*

# Upstream sets this so a failed fisheye focal-length initialisation can be
# supplied manually instead of aborting.
ENV KALIBR_MANUAL_FOCAL_LENGTH_INIT=1

# setup.bash passes the caller's positional parameters to _setup_util.py, so
# clear them before sourcing and restore the real command afterwards.
ENTRYPOINT ["/bin/bash", "-c", "set -e; args=(\"$@\"); set --; source /catkin_ws/devel/setup.bash; set -- \"${args[@]}\"; exec \"$@\"", "--"]
CMD ["bash"]
