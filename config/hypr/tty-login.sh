# Sourced by the login shell.
case $- in
    *i*)
        if [ "${XDG_VTNR:-}" = 1 ] && [ "${XDG_SESSION_TYPE:-}" = tty ] &&
            uwsm check may-start -q 1; then
            exec uwsm start hyprland.desktop
        fi
        ;;
esac
