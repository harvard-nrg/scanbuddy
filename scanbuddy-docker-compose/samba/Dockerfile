FROM rockylinux:8

RUN dnf install -y epel-release && \
    dnf install -y procps htop vim net-tools telnet psmisc
RUN dnf install -y samba samba-client

ARG SAMBA_USER=${SAMBA_USER}
ARG SAMBA_PASS=${SAMBA_PASS}
ARG SAMBA_GROUP=${SAMBA_USER}
ARG UID=${UID}
ARG GID=${GID}

RUN groupadd -f -g ${GID} ${SAMBA_GROUP}
RUN useradd ${SAMBA_USER} -u ${UID} -g ${GID} -m -s /bin/bash

RUN smbpasswd -a -n "${SAMBA_USER}"
RUN echo -e "${SAMBA_PASS}\n${SAMBA_PASS}" | smbpasswd "${SAMBA_USER}"
RUN smbpasswd -e "${SAMBA_USER}"

ENTRYPOINT ["smbd", "-F", "--no-process-group"]
