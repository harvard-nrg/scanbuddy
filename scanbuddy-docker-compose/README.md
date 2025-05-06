Customize `default.env`, save to a file named `.env`, then run

```bash
docker compose up
```

By default, this will start Scan Buddy, Redis, and NGINX reverse
proxy.

## Samba
If you want to start a Samba service container, add the `samba` profile

```bash
docker compose --profile samba up
```

## Developers
For developers, you may find it useful to mount your local development 
copy of the Scan Buddy into the container at the appropriate location

```bash
docker compose -f docker-compose.yaml -f docker-compose-devel.yaml up
```

