## Example config file
```yaml
app:
    title: Realtime fMRI Motion
    session_secret:
        env: SCANBUDDY_SESSION_KEY
    auth:
        user: scanbuddy
        pass:
            env: SCANBUDDY_PASS
params:
    coil_elements:
        bad:
            - receive_coil: Head_32
              coil_elements:  HEA
            - receive_coil: Head_32
              coil_elements: HEP
        message: |
            Session: {SESSION}
            Series: {SERIES}
            Coil: {RECEIVE_COIL}, {COIL_ELEMENTS}
            
            Detected an issue with head coil elements.

            1. Check head coil connection for debris or other obstructions.
            2. Reconnect head coil securely.
            3. Ensure that anterior and posterior coil elements are present.

            Call 867-5309 for further assistance.
```

## Example docker-compose.yml file

You can run a complete standalone system which serves a SMB share for the scanner to write to. Then, the entire system is just a `docker compose up` away:

```yaml
services:
  scanbuddy:
    image: scanbuddy:v0.1.9
    restart: unless-stopped
    network_mode: host
    depends_on:
      - samba
      - redis
    environment:
      SCANBUDDY_PASS: some_password
      SCANBUDDY_SESSION_KEY: some_password
    volumes:
      - /home/qc/scanbuddy:/scanbuddy
      - /home/qc/scanbuddy-data:/data
    command: ["-c", "/scanbuddy/config.yaml", "--folder", "/data", "--host", "0.0.0.0", "--port", "8080"]

  redis:
    image: redis:latest
    restart: unless-stopped
    network_mode: host

  samba:
    image: ghcr.io/servercontainers/samba
    restart: unless-stopped
    # you {c,sh}ould expose individual ports instead
    network_mode: host
    environment:
      SAMBA_CONF_LOG_LEVEL: 3
      WSDD2_DISABLE: 1
      AVAHI_DISABLE: 1
      NETBIOS_DISABLE: 1
      GROUP_fakegroup: 20
      ACCOUNT_scanbuddy: some_password
      UID_scanbuddy: 501
      GROUPS_scanbuddy: fakegroup
      SAMBA_VOLUME_CONFIG_scanbuddy: "[scanbuddy]; path=/data; valid users = scanbuddy; guest ok = no; read only = no; b\
rowseable = yes"
    volumes:
      - /home/qc/scanbuddy-data:/data

```
