FROM rockylinux:9

# install some base necessities
RUN dnf install -y git vim
RUN dnf install -y epel-release
RUN dnf install -y conda
RUN conda create -y -n python3.13t --override-channels -c conda-forge python-freethreading
RUN conda env config vars set PYTHON_GIL=0 -n python3.13t
RUN conda run -n python3.13t --no-capture-output python3 -m pip install git+https://github.com/harvard-nrg/scanbuddy.git
RUN conda run -n python3.13t start.py --help # ENTRYPOINT ["conda", "run", "-n", "python3.13t", "start.py"]
#RUN dnf install -y git vim python3.13 && \
#    alternatives --set python /usr/bin/python3

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

# compile and install dcm2niix (linux/amd64 and linux/arm64/v8)
ARG D2N_PREFIX="/sw/apps/dcm2niix"
ARG D2N_VERSION="1.0.20220720"
ARG D2N_URI="https://github.com/rordenlab/dcm2niix/archive/refs/tags/v${D2N_VERSION}.zip"
WORKDIR "/tmp"
RUN dnf install -y unzip cmake gcc-c++ && \
    dnf config-manager --set-enabled crb && \
    dnf install -y libstdc++-static && \
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

# install scanbuddy
ARG SB_PREFIX="/sw/apps/scanbuddy"
ARG SB_VERSION="v0.1.10"
RUN python3 -m venv "${SB_PREFIX}" && \
    dnf install -y gcc zlib-devel libjpeg-devel python3-tkinter && \
    "${SB_PREFIX}/bin/pip" install "git+https://github.com/harvard-nrg/scanbuddy.git@${SB_VERSION}"

# set up afni environment
ENV PATH="${AFNI_PREFIX}:${PATH}"

# set up dcm2niix environment f
ENV PATH="${D2N_PREFIX}:${PATH}"

# set up scanbuddy
ENV TERM="xterm-256color"

# expose port
EXPOSE 11112

ENTRYPOINT ["/sw/apps/scanbuddy/bin/start.py"]
