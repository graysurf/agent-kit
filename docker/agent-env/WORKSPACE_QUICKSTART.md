# Codex Workspace Quick Start

Short guide to create a new workspace and connect with VS Code.

## 1) Create a new workspace (example repo)

```sh
./docker/agent-env/bin/agent-workspace create graysurf/agent-kit --name agent-kit
```

Notes:

- `create` is an alias of `up`.

For private repos, provide a host token for the initial clone (not stored as a container env var):

```sh
read -s GH_TOKEN
export GH_TOKEN
./docker/agent-env/bin/agent-workspace create graysurf/agent-kit --name agent-kit --setup-git
unset GH_TOKEN
```

Find workspace names later:

```sh
./docker/agent-env/bin/agent-workspace ls
```

## 2) Connect with VS Code (Dev Containers)

1. Install the VS Code extensions: "Docker" and "Dev Containers".
2. Cmd+Shift+P -> "Dev Containers: Attach to Running Container..."
3. Pick `agent-ws-agent-kit`.
4. Open `/work/graysurf/agent-kit`.

## 3) Connect with VS Code (Remote Tunnels)

Use a short workspace name (<= 20 chars) so the tunnel name is valid.

Start the tunnel:

```sh
./docker/agent-env/bin/agent-workspace tunnel agent-kit --detach
```

Optional: machine output (stdout-only JSON; includes `tunnel_name` + `log_path`):

```sh
./docker/agent-env/bin/agent-workspace tunnel agent-kit --detach --output json
```

If this is your first run, you need to complete GitHub device login.

When using `--detach`, the device code is written to the tunnel log. Tail the log and follow the URL:

```sh
docker exec -it agent-ws-agent-kit bash -lc 'tail -f /home/agent/.agents-env/logs/code-tunnel.log'
```

Alternatively, print a new device code by running the login command:

```sh
docker exec -it agent-ws-agent-kit code tunnel user login --provider github
```

Tip: the command/log will show a code like `ABCD-EFGH` — enter that code at <https://github.com/login/device> (you do not paste it back into
the terminal).

Verify the tunnel is connected (expected: `"tunnel":"Connected"` and `"name":"agent-kit"`):

```sh
docker exec -it agent-ws-agent-kit code tunnel status
```

Note: the first VS Code connection may take a few minutes while the VS Code Server is downloaded inside the container (you may see
"Downloading VS Code Server...").

Connect from VS Code:

1. Cmd+Shift+P -> "Remote Tunnels: Connect to Tunnel..."
2. Select `agent-kit`.

## 4) Clean up

```sh
./docker/agent-env/bin/agent-workspace stop agent-kit
./docker/agent-env/bin/agent-workspace rm agent-kit
```
