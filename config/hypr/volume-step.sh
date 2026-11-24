#!/bin/sh
case "$1" in
    up) sign=+ ;;
    down) sign=- ;;
    *) exit 2 ;;
esac

exec 9>>"$XDG_RUNTIME_DIR/hypr-volume-step.lock"
flock 9 || exit 1

sink=$(pactl get-default-sink) || exit 1
if [ "$sign" = + ]; then
    volume=$(LC_ALL=C pactl get-sink-volume "$sink") || exit 1
    step_to_apply=$(printf '%s\n' "$volume" | awk '
        /^Volume:/ {
            for (i = 1; i <= NF; i++)
                if ($i ~ /^[0-9]+%$/ && $i + 0 > max) max = $i + 0
            if (max < 100) print 1
        }
    ')
else
    step_to_apply=1
fi

if [ -n "$step_to_apply" ]; then
    pactl set-sink-volume "$sink" "$sign$step_to_apply%" || exit 1
fi
