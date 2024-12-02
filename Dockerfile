FROM rockylinux:8

# Install necessary packages
RUN dnf install -y git vim tcsh libpng15 motif make curl clang zlib-devel \
    libXt-devel libXext-devel expat-devel motif-devel f2c unzip cmake gcc-c++ \
    epel-release && \
    dnf --enablerepo=powertools install -y libstdc++-static

# Install Mambaforge
WORKDIR /tmp
RUN curl -L https://github.com/conda-forge/miniforge/releases/download/24.9.2-0/Mambaforge-24.9.2-0-Linux-x86_64.sh -o Mambaforge-24.9.2-0.sh && \
    chmod 755 Mambaforge-24.9.2-0.sh && \
    ./Mambaforge-24.9.2-0.sh -b -p /opt/conda && \
    rm Mambaforge-24.9.2-0.sh
ENV PATH=/opt/conda/bin:$PATH

# Create a Conda environment with Python 3.13
RUN conda create -n py313 python=3.13 python-freethreading -c conda-forge/label/python_rc -c conda-forge && \
    echo "conda activate py313" >> ~/.bashrc
ENV CONDA_DEFAULT_ENV=py313
ENV PATH /opt/conda/envs/py313/bin:$PATH

# Verify Python version
RUN python --version

# Create a home directory
RUN mkdir -p /home/scanbuddy
ENV HOME=/home/scanbuddy

# Compile and install 3dvolreg from AFNI (linux/amd64 and linux/arm64/v8)
ARG AFNI_PREFIX="/sw/apps/afni"
ARG AFNI_URI="https://github.com/afni/afni"
WORKDIR /tmp
RUN git clone "${AFNI_URI}"
WORKDIR afni/src
RUN cp other_builds/Makefile.linux_ubuntu_22_64 Makefile && \
    make libmri.a 3dvolreg && \
    mkdir -p "${AFNI_PREFIX}" && \
    mv 3dvolreg "${AFNI_PREFIX}" && \
    rm -r /tmp/afni

# Compile and install dcm2niix (linux/amd64 and linux/arm64/v8)
ARG D2N_PREFIX="/sw/apps/dcm2niix"
ARG D2N_VERSION="1.0.20220720"
ARG D2N_URI="https://github.com/rordenlab/dcm2niix/archive/refs/tags/v${D2N_VERSION}.zip"
WORKDIR /tmp
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

# Install scanbuddy
ARG SB_PREFIX="/sw/apps/scanbuddy"
ARG SB_VERSION="v0.1.7"
RUN python -m venv "${SB_PREFIX}" && \
    dnf install -y gcc zlib-devel libjpeg-devel python39-tkinter && \
    "${SB_PREFIX}/bin/pip" install "git+https://github.com/harvard-nrg/scanbuddy.git@${SB_VERSION}"

# Set up AFNI environment
ENV PATH="${AFNI_PREFIX}:${PATH}"

# Set up dcm2niix environment
ENV PATH="${D2N_PREFIX}:${PATH}"

# Set up scanbuddy
ENV TERM="xterm-256color"

# Expose port
EXPOSE 11112

ENTRYPOINT ["/sw/apps/scanbuddy/bin/start.py"]