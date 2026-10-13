#!/bin/sh
# Run one of this plugin's Python hook scripts with the first working Python 3.
#
# Claude Code runs shell-form hooks with sh on macOS / Linux and Git Bash on Windows.
# Windows installs from python.org usually provide `python` and `py`, not `python3`,
# and `python3` may be the Microsoft Store stub, so each candidate is probed by
# actually running it instead of trusting PATH lookup.
for py in python3 python "py -3"; do
  # $py is unquoted on purpose so that "py -3" splits into command + flag.
  if $py -c 'import sys; sys.exit(sys.version_info < (3, 8))' </dev/null >/dev/null 2>&1; then
    exec $py "$@"
  fi
done
echo "emb-repo: 找不到可用的 Python 3.8+（已尝试 python3、python、py -3），hook 未运行。请安装 Python 并加入 PATH。" >&2
exit 1
