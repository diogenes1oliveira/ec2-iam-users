#!/bin/bash

set -o pipefail
PROGRAM_NAME="$0"

usage() {
  cat <<EOF
ssh-authorize-via-iam
=====================

Fetches the public SSH keys for the authorized SSH user via IAM.

This script is supposed to be used with AuthorizedKeysCommand.

Usage:
  $PROGRAM_NAME USERNAME

Parameters:
  USER_NAME        name of the user to fetch

Environment:
  FETCH_COMMAND    command to be used to fetch the public keys. Defaults to
                   FETCH_COMMAND='fetch-public-keys-from-iam'

Exit codes:
  BAD_VALUE=1  invalid parameter value
  NOT_FOUND=4  user not found in the IAM group

Requirements:
  - pip: [ awscli ]
  - apt: [ jq ]
EOF
}


BAD_VALUE=1
NOT_FOUND=4

main() {
  if [[ -z "$FETCH_COMMAND" ]]; then
    FETCH_COMMAND='fetch-public-keys-from-iam'
  fi

  if [[ "$USERNAME" != {{ ssh_username | quote }} ]]; then
    echo "User $USERNAME can't login via SSH" >&2
    exit $NOT_FOUND
  fi

  $FETCH_COMMAND "$USERNAME"
  exit $?
}

OPTS=$(getopt -o '-h' --long 'help' -- "$@")

if [[ "$?" != 0 ]]; then
  echo 'Error: failed to parse the command-line arguments.' >&2
  echo >&2
  usage >&2
  exit $BAD_VALUE
fi

eval set -- "$OPTS"

while true; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      break
  esac

  shift
done

USERNAME="$1"

if [[ ! "$USERNAME" =~ ^[a-zA-Z_][a-zA-Z0-9_-]*{1,64}$ ]]; then
  echo "Invalid Linux username: ${USERNAME}" >&2
  exit $BAD_VALUE
fi

main

