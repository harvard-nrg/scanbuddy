FROM ubuntu:focal

# create a home directory
RUN mkdir -p /home/scanbuddy
ENV HOME=/home/scanbuddy

RUN apt-get update

RUN apt-get install -y git

# compile and install 3dvolreg from AFNI (linux/amd64 and linux/arm64/v8)
ARG AFNI_PREFIX="/sw/apps/afni"
ARG AFNI_URI="https://github.com/afni/afni"
WORKDIR /tmp
RUN git clone "${AFNI_URI}"
WORKDIR afni/src
ARG DEBIAN_FRONTEND=noninteractive
ARG TZ="America/New_York"
RUN apt-get install -y make cmake
RUN apt-get install -y zlib1g-dev libxt-dev libxtst-dev libexpat1-dev libmotif-dev
RUN cp other_builds/Makefile.linux_ubuntu_22_64 Makefile && \
    make libmri.a 3dvolreg && \
    mkdir -p "${AFNI_PREFIX}" && \
    mv 3dvolreg "${AFNI_PREFIX}" && \
    rm -r /tmp/afni
ENV PATH="${AFNI_PREFIX}:${PATH}"

# compile and install dcm2niix (linux/amd64 and linux/arm64/v8)
ARG D2N_PREFIX="/sw/apps/dcm2niix"
#ARG D2N_VERSION="1.0.20220720"
ARG D2N_VERSION="1.0.20241211"
ARG D2N_URI="https://github.com/rordenlab/dcm2niix/archive/refs/tags/v${D2N_VERSION}.zip"
WORKDIR "/tmp"
RUN apt-get install -y curl unzip g++ vim-nox
RUN curl -sL "${D2N_URI}" -o "dcm2niix_src.zip" && \
    unzip "dcm2niix_src.zip" && \
    rm "dcm2niix_src.zip" && \
    mkdir "dcm2niix-${D2N_VERSION}/build"
WORKDIR "/tmp/dcm2niix-${D2N_VERSION}/build"
RUN cmake .. && \
    make && \
    mkdir -p "${D2N_PREFIX}" && \
    cp bin/dcm2niix "${D2N_PREFIX}" && \
    rm -r "/tmp/dcm2niix-${D2N_VERSION}"
ENV PATH="${D2N_PREFIX}:${PATH}"

# install miniforge
ARG MFG_PREFIX="/sw/miniforge"
WORKDIR "/tmp"
RUN curl -sL "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" -o "miniforge.sh"
RUN bash "miniforge.sh" -b -p "${MFG_PREFIX}"
RUN rm "miniforge.sh"
ENV PATH="${MFG_PREFIX}/bin:${PATH}"

# install scanbuddy
RUN mamba create -y -n python3.13t --override-channels -c conda-forge python-freethreading
RUN mamba env config vars set PYTHON_GIL=0 -n python3.13t
ARG SB_VERSION="main"
COPY requirements.txt /tmp/requirements.txt
RUN apt-get install -y libjpeg-dev libf2c2-dev
RUN mamba run -n python3.13t --no-capture-output python3 -m pip install -r /tmp/requirements.txt
RUN mamba run -n python3.13t --no-capture-output python3 -m pip install "git+https://github.com/harvard-nrg/scanbuddy.git@${SB_VERSION}"

ENTRYPOINT ["mamba", "run", "-n", "python3.13t", "--no-capture-output", "start.py"]
