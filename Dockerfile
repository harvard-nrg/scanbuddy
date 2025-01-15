FROM fedora:41

# install some base necessities
RUN dnf install -y git vim dcm2niix

# create a home directory
RUN mkdir -p /home/scanbuddy
ENV HOME=/home/scanbuddy

# compile and install 3dvolreg from AFNI (linux/amd64 and linux/arm64/v8)
ARG AFNI_PREFIX="/sw/apps/afni"
ARG AFNI_URI="https://github.com/afni/afni"
WORKDIR /tmp
RUN dnf install -y --allowerasing curl tcsh libpng15 motif && \
    dnf install -y make clang zlib-devel libXt-devel libXext-devel expat-devel motif-devel f2c && \
    git clone "${AFNI_URI}"
WORKDIR afni/src
RUN cp other_builds/Makefile.linux_ubuntu_22_64 Makefile && \
    make libmri.a 3dvolreg && \
    mkdir -p "${AFNI_PREFIX}" && \
    mv 3dvolreg "${AFNI_PREFIX}" && \
    rm -r /tmp/afni
ENV PATH="${AFNI_PREFIX}:${PATH}"

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
RUN mamba run -n python3.13t --no-capture-output python3 -m pip install "git+https://github.com/harvard-nrg/scanbuddy.git@${SB_VERSION}"

ENTRYPOINT ["mamba", "run", "-n", "python3.13t", "--no-capture-output", "start.py"]
