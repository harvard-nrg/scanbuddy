# Docker Compse Guide

Scan Buddy is inherently a multi-container application, which can be 
a bit cumbersome to deploy. To address this, we've been working on a 
way to streamline deployment using [Docker Compose][docker compose].

## System Requirements

This deployment process has been tested using [Docker Engine][docker linux] on 
Linux and [Docker Desktop for Mac][docker macos] on macOS with Apple Silicon.

Please install Docker Engine or Docker Desktop before moving forward.

# Customize .env file
Customize the `default.env` file provided within this repository and save it 
to a file named `.env`. Here's a description of customizable properties

> [!WARNING]
> If you are exporting a Samba share(s) from the same machine running Scan 
> Buddy, be sure to set `MEM_LIMIT` and `MEM_SWAP_LIMIT` well below the 
> available memory.
>
> If the machine exporting your Samba shares runs out of memory, the scanner 
> may experience difficulty writing files to the exported share, which could 
> result in scanner instability.

| Property Name           | Description                                  | Example                         |
|-------------------------|----------------------------------------------|---------------------------------|
| `SCANBUDDY_VERSION`     | Scan Buddy version `0.2.6` or greater        | `0.2.6`                         |
| `BIND_ADDR`             | Bind Scan Buddy to this network address      | `127.0.0.1`                     |  
| `BIND_PORT`             | Bind Scan Buddy to this port                 | `8000`                          |
| `INCOMING_DIR`          | Local directory to export to the scanner     | `/path/to/scanner-data`         |
| `CONFIG`                | Local path to Scan Buddy [config][sb config] | `/path/to/scanbuddy.yaml`       |
| `SCANBUDDY_USER`        | Scan Buddy (Basic Auth) username             | `scanbuddy`                     |
| `SCANBUDDY_PASS`        | Scan Buddy (Basic Auth) password             | `*********`                     |
| `SCANBUDDY_SESSION_KEY` | Scan Buddy session key                       | `*********`                     |
| `UID`                   | Run Scan Buddy with this UID                 | `501`                           |
| `GID`                   | Run Scan Buddy with this GID                 | `20`                            |
| `MEM_LIMIT`             | [Memory limit][mem_limit]                    | `10g`                           |
| `MEM_SWAP_LIMIT`        | [Memory + swap limit][memswap_limit]         | `15g`                           |
| `CPU_LIMIT`             | [CPU limit][cpus] (`0.00` means no limit)    | `0.00`                          |
| `SAMBA_PASS`            | Samba password (default user `scanbuddy`)    | `*********`                     |
| `REDIS_VERSION`         | Redis container version (keep default)       | `7.4.3-bookworm`                |
| `NGINX_VERSION`         | Nginx container version (keep default)       | `1.19-alpine-perl`              |
| `SAMBA_VERSION`         | Samba container version (keep default)       | `smbd-wsdd2-a3.21.3-s4.20.6-r1` |

## Installing and running Scan Buddy

Once you've customized and saved your `.env` file, run the following command 
to download and run a complete Scan Buddy deployment

> [!NOTE]
> Keep reading if you also want to start a Samba container

```bash
docker compose up -d
```

The container images needed to run a complete Scan Buddy deployment will only 
be downloaded the first time you run this command.

### Running a Samba container

By default, `docker compose up` will only start Scan Buddy, Redis, and Nginx 
containers. To start a Samba container, pass the additional `--profile samba` 
argument

> [!NOTE]
> The default Samba username will be `scanbuddy` and shares will be exported 
> with the names `bold` and `localizer`

```bash
docker compose --profile samba up -d
```

## Stopping Scan Buddy

Run the following command to stop Scan Buddy

> [!TIP]
> Remember to use `docker compose --profile samba down` if you started a Samba 
> container

```bash
docker compose down
```

## Monitoring the Scan Buddy logs

Run the following command to watch Scan Buddy logs in realtime

```bash
docker compose logs -f scanbuddy-web
```

## Developer tips

For developers, you may find it useful to mount your local development 
copy of Scan Buddy into the container at the appropriate location, rather 
than having to rebuild the container

```bash
docker compose -f docker-compose.yaml -f docker-compose-devel.yaml up
```

[docker compose]: https://docs.docker.com/compose
[docker linux]: https://docs.docker.com/engine/install
[docker macos]: https://docs.docker.com/desktop/setup/install/mac-install
[mem_limit]: https://docs.docker.com/reference/compose-file/services/#mem_limit
[memswap_limit]: https://docs.docker.com/reference/compose-file/services/#memswap_limit
[cpus]: https://docs.docker.com/reference/compose-file/services/#cpus
[sb config]: https://github.com/harvard-nrg/scanbuddy/blob/main/example-config.yaml

