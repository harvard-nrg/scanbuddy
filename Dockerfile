FROM rockylinux:8

# install some base necessities
RUN dnf install -y git vim

# create a home directory
RUN mkdir -p /home/scanbuddy
ENV HOME=/home/scanbuddy

# compile and install 3dvolreg from AFNI (linux/amd64 and linux/arm64/v8)
ARG AFNI_PREFIX="/sw/apps/afni"
ARG AFNI_URI="https://github.com/afni/afni"
WORKDIR /tmp
RUN dnf install -y epel-release && \
    dnf install -y --allowerasing curl tcsh libpng15 motif && \
    dnf install -y make clang zlib-devel libXt-devel libXext-devel expat-devel motif-devel f2c && \
    git clone "${AFNI_URI}"
WORKDIR afni/src
RUN cp other_builds/Makefile.linux_ubuntu_22_64 Makefile && \
    make libmri.a 3dvolreg && \
    mkdir -p "${AFNI_PREFIX}" && \
    mv 3dvolreg "${AFNI_PREFIX}" && \
    rm -r /tmp/afni
ENV PATH="${AFNI_PREFIX}:${PATH}"

# compile and install dcm2niix (linux/amd64 and linux/arm64/v8)
ARG D2N_PREFIX="/sw/apps/dcm2niix"
ARG D2N_VERSION="1.0.20220720"
ARG D2N_URI="https://github.com/rordenlab/dcm2niix/archive/refs/tags/v${D2N_VERSION}.zip"
WORKDIR /tmp
RUN dnf install -y unzip cmake gcc-c++ && \
    dnf --enablerepo=powertools install -y libstdc++-static && \
    curl -sL "${D2N_URI}" -o "dcm2niix_src.zip" && \
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
WORKDIR /tmp
RUN curl -sL "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-$(uname -m).sh" -o "miniforge.sh"
RUN bash "miniforge.sh" -b -p "${MFG_PREFIX}" && \
    rm "miniforge.sh"
ENV PATH="${MFG_PREFIX}/bin:${PATH}"

# install specific mamba version (1.5.12)
RUN conda install -y -n base -c conda-forge mamba=1.5.12

# install scanbuddy with python-freethreading
RUN mamba create -y -n python3.13t --override-channels -c conda-forge python-freethreading=3.13.1
RUN mamba env config vars set PYTHON_GIL=0 -n python3.13t
ARG SB_VERSION="0.2.5"
RUN mamba run -n python3.13t --no-capture-output python3 -m pip install "git+https://github.com/harvard-nrg/scanbuddy.git@${SB_VERSION}"

ENTRYPOINT ["mamba", "run", "-n", "python3.13t", "--no-capture-output", "start.py"]
