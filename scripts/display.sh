#!/usr/bin/env bash
# Source from the kiosk/session to select the attached DSI panel and its size.
# A session may source this before executing the kiosk: configure outputs once.
if [ "${TOUCHUI_DISPLAY_READY:-0}" = 1 ]; then return 0; fi
TOUCHUI_WIDTH=800
TOUCHUI_HEIGHT=480
if [ -n "${DISPLAY:-}" ] && command -v xrandr >/dev/null 2>&1; then
    TOUCHUI_DSI=$(xrandr --query | awk '$1 ~ /^DSI-/ && $2 == "connected" {print $1; exit}')
    if [ -n "$TOUCHUI_DSI" ]; then
        # Old HDMI hotplug overrides can otherwise enlarge the desktop to 800x800.
        TOUCHUI_OUTPUT_ARGS=(--output "$TOUCHUI_DSI" --auto --primary --rotate normal --pos 0x0)
        while read -r output; do
            [ -n "$output" ] && TOUCHUI_OUTPUT_ARGS+=(--output "$output" --off)
        done < <(xrandr --query | awk '$1 ~ /^HDMI-/ && $2 == "connected" {print $1}')
        xrandr "${TOUCHUI_OUTPUT_ARGS[@]}"
        if command -v xinput >/dev/null 2>&1; then
            while read -r device; do
                case "$device" in
                    *ft5x06*|*FT5406*|*raspberrypi-ts*)
                        xinput map-to-output "$device" "$TOUCHUI_DSI" || true ;;
                esac
            done < <(xinput list --name-only)
        fi
    fi
    read -r width height < <(xrandr --current | sed -n 's/.*current \([0-9]*\) x \([0-9]*\),.*/\1 \2/p')
    if [[ "${width:-}" =~ ^[0-9]+$ && "${height:-}" =~ ^[0-9]+$ ]]; then
        TOUCHUI_WIDTH=$width
        TOUCHUI_HEIGHT=$height
    fi
fi
TOUCHUI_DISPLAY_READY=1
export TOUCHUI_WIDTH TOUCHUI_HEIGHT TOUCHUI_DISPLAY_READY
