#!/usr/bin/env bash
# A single kiosk owner, independent of Internet/WiFi readiness.
set -u
export DISPLAY="${DISPLAY:-:0}"
RUNTIME="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
if [ ! -d "$RUNTIME" ]; then RUNTIME="/tmp/kali-touch-$(id -u)"; mkdir -p "$RUNTIME"; chmod 700 "$RUNTIME"; fi
exec 9>"$RUNTIME/kali-touch-kiosk.lock"
flock -n 9 || exit 0
[ ! -f /etc/kali-touch-ui/kiosk.conf ] || source /etc/kali-touch-ui/kiosk.conf
source /opt/kali-touch-ui/scripts/display.sh
xset s off -dpms >/dev/null 2>&1 || true
xset dpms force on >/dev/null 2>&1 || true
BASE_URL="${TOUCHUI_URL:-http://127.0.0.1:8080}"
BASE_URL="${BASE_URL%/}"
URL="$BASE_URL"
case "${TOUCHUI_EDITION:-7inch}" in
    7inch|4inch|35inch)
        case "$URL" in *\?*) URL="${URL}&edition=${TOUCHUI_EDITION:-7inch}" ;; *) URL="${URL}?edition=${TOUCHUI_EDITION:-7inch}" ;; esac ;;
esac
# The early Darksec animation has already played: don't replay a second boot.
if [ "${TOUCHUI_BOOT_SPLASH:-browser}" = system ]; then
    case "$URL" in *\?*) URL="${URL}&splash=handoff" ;; *) URL="${URL}?splash=handoff" ;; esac
fi
BROWSER=""
for b in chromium chromium-browser google-chrome; do
    if command -v "$b" >/dev/null 2>&1; then BROWSER="$b"; break; fi
done
[ -n "$BROWSER" ] || { echo 'Kali Touch: Chromium is not installed' >&2; exit 1; }
# Wait only for local static content. The page retries API startup itself.
until curl -fsS --connect-timeout 1 --max-time 1 -o /dev/null "$BASE_URL/" 2>/dev/null; do
    sleep .25
done
RESTART_DELAY="${TOUCHUI_RESTART_DELAY:-3}"
trap 'kill "${BROWSER_PID:-}" 2>/dev/null || true; exit' TERM INT
while true; do
    "$BROWSER" --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble \
        --no-first-run --disable-component-update --hide-scrollbars \
        --disable-features=TranslateUI,AutofillServerCommunication,MediaRouter \
        --touch-events=enabled --disable-gpu --disable-gpu-compositing --use-gl=swiftshader \
        --disable-software-rasterizer=0 --enable-unsafe-swiftshader --password-store=basic \
        --force-device-scale-factor=1 --disable-pinch --overscroll-history-navigation-disabled \
        --pull-to-refresh=0 --window-size="$TOUCHUI_WIDTH,$TOUCHUI_HEIGHT" --window-position=0,0 \
        --app="$URL" 9>&- 2>/tmp/kali-touch-kiosk.log &
    BROWSER_PID=$!
    # Only size a new window once; repeated raises can fight the Social browser.
    WINDOW_SIZED=0
    while kill -0 "$BROWSER_PID" 2>/dev/null; do
        if [ "$WINDOW_SIZED" = 0 ]; then
            WID=$(xdotool search --onlyvisible --name '^Kali Touch UI$' 2>/dev/null | head -1)
            if [ -n "$WID" ]; then
                xprop -id "$WID" -f _MOTIF_WM_HINTS 32c -set _MOTIF_WM_HINTS 0x2,0x0,0x0,0x0,0x0 2>/dev/null || true
                xdotool windowsize "$WID" "$TOUCHUI_WIDTH" "$TOUCHUI_HEIGHT" windowmove "$WID" 0 0 windowfocus "$WID" 2>/dev/null || true
                WINDOW_SIZED=1
            fi
        fi
        sleep 1
    done
    wait "$BROWSER_PID" 2>/dev/null || true
    echo "Kali Touch: browser exited; restarting in ${RESTART_DELAY}s" >&2
    sleep "$RESTART_DELAY"
done
