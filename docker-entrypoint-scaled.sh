#!/bin/sh
set -e

CONTAINER_ID=$(hostname)

# ------- your untouched SERVICE_HOST block -------
if [ -z "$SERVICE_HOST" ]; then
  CGROUP_NAME=$(sed -n 's/.*docker-\([^.]*\).*/\1/p' /proc/self/cgroup | head -n1)
  [ -z "$CGROUP_NAME" ] && CGROUP_NAME=$(sed -n 's|.*/docker/\([^/]*\).*|\1|p' /proc/self/cgroup | head -n1)

  if [ -z "$CGROUP_NAME" ] || [ "$CGROUP_NAME" = "$CONTAINER_ID" ]; then
    export SERVICE_HOST="$CONTAINER_ID"
  else
    export SERVICE_HOST="$CGROUP_NAME"
  fi
fi
echo "[WRAPPER] SERVICE_HOST=$SERVICE_HOST"


# ---------- 100 ms poll until discovery answers ----------
SD_HOST=$(
  printf '%s\n' "${SERVICE_DISCOVERY_URL}" "${DISCOVERY_URL}" |
  grep -E '^https?://' | head -n1 |
  sed -e 's|^[^/]*://||' -e 's|/.*||'
)
: "${SD_HOST:=fafcab_service_discovery:8001}"   # final fallback

echo "[WRAPPER] waiting for $SD_HOST …"
while ! wget -q -T 1 -O - "http://${SD_HOST}/api/services" >/dev/null 2>&1; do
  sleep 0.1
done
echo "[WRAPPER] discovery reachable – starting service"
# --------------------------------------------------------


# -------------------------------------------------

# 1.  images that ship a classic docker-entrypoint.sh anywhere
for ep in /docker-entrypoint.sh /app/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh; do
  [ -x "$ep" ] && echo "[WRAPPER] found entrypoint script $ep" && exec "$ep" "$@"
done

# 2.  Elixir release:  /app/bin/<release>  (CMD was ["start"] or similar)
if [ -d /app/bin ]; then
  for exe in /app/bin/*; do
    [ -x "$exe" ] || continue
    case "${exe##*/}" in
      migrate|eval|rpc|remote|console|ping|version|stop) continue ;;
    esac
    # use the CMD passed by the image (e.g. "start") or default to "start"
    [ $# -eq 0 ] && set -- start
    echo "[WRAPPER] Elixir release: $exe $*" && exec "$exe" "$@"
  done
fi

# 3.  Java fat-jar images (ENTRYPOINT ["java","-jar","/app/app.jar"])
for j in /app/app.jar /app/*.jar /*.jar; do
  [ -f "$j" ] && echo "[WRAPPER] java -jar $j $*" && exec java -jar "$j" "$@"
done

# 4.  images that only have a CMD (no ENTRYPOINT) – uvicorn, uv run, npm start …
#     we simply execute the CMD that the image declares
if [ $# -gt 0 ]; then
  echo "[WRAPPER] CMD only: $*" && exec "$@"
fi

# 5.  last-ditch fallback so the container does not exit 0
echo "[WRAPPER] nothing matched – starting idle shell" && exec /bin/sh