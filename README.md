# Rocket League Dual Split Screen in Linux (KDE Plasma with Wayland)

Simple helper script for changing the TASystemSettings.ini file and (optionally) resizing two monitors for playing Rocket League using split screen.

The script only works for Linux, using KDE Plasma and Wayland. With some tweaks, you can generalize it for other OS's. Feel free to do so.

The script is dependency-free, you only need Python 3. However, it calls to `find` and `kscreen-doctor` executables.

```shell
# Make the script executable (optional)
$ chmod +x rlds.py

# Apply changes for splitscreen
$ ./rlds.py    # or `python rlds.py`

# Revert changes
$ ./rlds.py --revert
```
