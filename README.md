# UPnPPort

Maintains port forwarding in UPnP compatible routers.

## Install

```
pip install UPnPPort
```

This installs a script called `upnpport`.

## Example use case

With the following configuration file, the daemon will create two
forwarding rules `80 -> 8888` and `22 -> 22`.

```yaml
- port: 8888
  external_port: 80
  protocol: tcp
- port: 22
  protocol: tcp
```

The internal ip used is the one running the daemon.

## Configuration

Configuration files are searched in one of the following
locations. Last configuration file found takes precendence.
* `/etc/upnpport/upnpport.yaml`
* `~/.config/upnpport/upnpport.yaml`
* `./config/upnpport.yaml`

You can override the above list of searched paths by giving the
`--config_files=path[,path,...]` argument.

Adding or removing rules to a configuration file is done by using the
`configure` argument:

```
upnpport <config_file.yaml> add [--protocol {tcp,udp}] [--external_port EXTERNAL_PORT] port

upnpport <config_file.yaml> del [--protocol {tcp,udp}] [--external_port EXTERNAL_PORT] port
```

## Run

Running the daemon is done by using the `run` argument:

```
upnpport run [--config_files CONFIG_FILES]
```

## Using systemd

The daemon can start when the system starts by creating a systemd unit
file like the following one in `/etc/systemd/system/upnpport.service`.

```
[Unit]
Description=UPnPPort service
After=network.target

[Service]
User=upnpport
Group=upnpport
ExecStart=/usr/bin/upnpport run
ExecReload=/bin/kill -s usr1 $MAINPID

[Install]
WantedBy=default.target
```

I advice running the daemon with a non-root user. A system user can be
created with `useradd --system upnpport`.
