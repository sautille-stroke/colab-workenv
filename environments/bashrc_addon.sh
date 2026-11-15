#!/usr/bin/env bash
# Handy terminal shortcuts and environment definitions for DervGen Colab workspace

export WORKSPACE_ROOT="${WORKSPACE_ROOT:-/content/workspace}"
export PATH="${WORKSPACE_ROOT}/scripts:${PATH}"

# Terminal Aliases
alias ll='ls -alF --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'

alias gs='git status -sb'
alias ga='git add'
alias gc='git commit -m'
alias gp='git push'
alias gl='git log --oneline --graph --decorate -n 15'
alias gd='git diff'

# GPU & System monitoring
alias gpu-watch='watch -n 1 nvidia-smi'
alias mem-check='free -h && df -h /content'

# Bazel shortcuts
alias bb='bazel build'
alias bt='bazel test'
alias br='bazel run'
alias bclean='bazel clean --expunge'

# Workspace sync shortcuts
alias wsync='bash ${WORKSPACE_ROOT}/colab/git_sync.sh'
alias wstatus='bash ${WORKSPACE_ROOT}/scripts/check_env.sh'
