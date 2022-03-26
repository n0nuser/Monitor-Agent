# Monitor - Agent

Final Degree Project - Host to monitor

## Uvicorn configuration

In `settings.json` you could pass this parameters to Uvicorn server:

```python
host: str
port: int
uds: str
fd: int
loop: str
http: str
ws: str
ws_max_size: int
ws_ping_interval: float
ws_ping_timeout: float
ws_per_message_deflate: bool
lifespan: str
debug: bool
reload: bool
reload_dirs: typing.List[str]
reload_includes: typing.List[str]
reload_excludes: typing.List[str]
reload_delay: float
workers: int
env_file: str
log_config: str
log_level: str
access_log: bool
proxy_headers: bool
server_header: bool
date_header: bool
forwarded_allow_ips: str
root_path: str
limit_concurrency: int
backlog: int
limit_max_requests: int
timeout_keep_alive: int
ssl_keyfile: str
ssl_certfile: str
ssl_keyfile_password: str
ssl_version: int
ssl_cert_reqs: int
ssl_ca_certs: str
ssl_ciphers: str
headers: typing.List[str]
use_colors: bool
app_dir: str
factory: bool
```

More information in their webpage - [Uvicorn Settings](https://www.uvicorn.org/settings/).

> :warning: If any parameters is incorrect the server will crash.
