#!/bin/bash

set -o pipefail
PROGRAM_NAME="$0"

usage() {
  cat <<EOF
fetch-public-keys-from-iam
==========================

Fetches the public SSH keys from the specified IAM user, as long as it
belongs to the specified IAM group.

Usage:
  $PROGRAM_NAME [-g=GROUP_NAME] [-m=N] IAM_USER

Parameters:
  -g, --group     restrict to users of this IAM group (default: {{ iam_group | quote }})
  -m, --max-keys  maximum number of keys to fetch (default: {{ max_ssh_keys }}).
                  IAM limits in 5 the number of public SSH keys for a user.
  IAM_USER        name of the user to fetch

Environment variables:
  ENDPOINT_URL        endpoint of the AWS service. Useful for local testing.
  AWS_DEFAULT_REGION  AWS region (default: {{ region }})

Exit codes:
  BAD_VALUE=1              invalid parameter value
  API_ERROR=2              error while calling the AWS APIs
  NOT_FOUND=4              user not found in the IAM group
  NO_KEYS=8                no active public SSH keys were found
  MISSING_REQUIREMENTS=16  missing jq or aws

Requirements:
  - pip: [ awscli ]
  - apt: [ jq ]
EOF
}

BAD_VALUE=1
API_ERROR=2
NOT_FOUND=4
NO_KEYS=8
MISSING_REQUIREMENTS=16

DEBUG=false
MAX_KEYS="{{ max_ssh_keys | quote }}"
IAM_USER=
IAM_GROUP="{{ iam_group | quote }}"
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-"{{ region }}"}

main() {
  check-requirements
  check-user-and-group
  fetch-public-key-ids

  for KEY_ID in "$KEY_IDS_OF_USER"; do
    aws-iam-cmd get-ssh-public-key \
      --user-name "$IAM_USER" \
      --ssh-public-key-id "$KEY_ID" \
      --encoding SSH | \
    jq -r '.SSHPublicKey.SSHPublicKeyBody'

    if [[ "$?" != 0 ]]; then
      echo "Couldn't fetch the public SSH key $KEY_ID" >&2
      exit $API_ERROR
    fi
  done
}

aws-iam-cmd() {
  if [[ -z "$ENDPOINT_URL" ]]; then
    aws iam "$@"
  else
    aws --endpoint-url "$ENDPOINT_URL" iam "$@"
  fi
}

check-requirements() {
  if ! jq --version; then
    echo "Couldn't find jq. Is it installed and available in the \$PATH?" >&2
    exit $MISSING_REQUIREMENTS
  fi
  
  if ! aws --version; then
    echo "Couldn't find aws. Is it installed and available in the \$PATH?" >&2
    exit $MISSING_REQUIREMENTS
  fi
}

check-user-and-group() {
  IAM_GET_GROUP_CMD=$(
    aws-iam-cmd get-group --group-name "$IAM_GROUP" \
    --no-paginate --query "Users[?UserName=='$IAM_USER']" 2>&1
  )
  CODE=$?

  if [[ "$CODE" == 0 ]]; then
    IAM_USER_COUNT=$(echo "$IAM_GET_GROUP_CMD" | jq length)

    if [[ "$IAM_USER_COUNT" == 0 ]]; then
      echo "No such user '$IAM_USER' in the group '$IAM_GROUP'" >&2
      exit $NOT_FOUND
    fi
  elif echo "$IAM_GET_GROUP_CMD" | grep '(NoSuchEntity)'; then
    echo "No such group '$IAM_GROUP'" >&2
    exit $NOT_FOUND
  else
    echo "$IAM_GET_GROUP_CMD" >&2
    exit $API_ERROR
  fi

}

fetch-public-key-ids() {
  KEY_IDS_OF_USER=$(
    aws-iam-cmd list-ssh-public-keys --user-name "$IAM_USER" --no-paginate \
      --query 'SSHPublicKeys[?Status==`Active`]' --max-items "$MAX_KEYS" \
    | jq -r '.[].SSHPublicKeyId'
  )

  if [[ $? != 0 ]]; then
    echo "Failed to call the aws iam list-ssh-public-keys command from the AWS CLI." >&2
    exit $API_ERROR
  fi
  
  if [[ -z "$KEY_IDS_OF_USER" ]]; then
    echo "Error: no active SSH key found for user $IAM_USER" >&2
    exit $NO_KEYS
  fi

}

OPTS=$(getopt -o -hgm --long help,group:,max-keys: -- "$@")

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
    -g|--group)
      shift
      IAM_GROUP="$1"
      if [[ ! "$IAM_GROUP" =~ ^[a-zA-Z0-9=,@_+.-]{1,64}$ ]]; then
        echo "Invalid IAM group name: ${IAM_GROUP}" >&2
        exit $BAD_VALUE
      fi
      ;;
    -m|max-keys)
      shift
      MAX_KEYS="$1"
      if [[ ! "$MAX_KEYS" =~ ^[12345]$ ]]; then
        echo "Invalid number of max keys: ${MAX_KEYS}, must be an integer between 1 and 5" >&2
        exit $BAD_VALUE
      fi
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

IAM_USER="$1"

if [[ ! "$IAM_USER" =~ ^[a-zA-Z0-9=,@_+.-]{1,64}$ ]]; then
  echo "Invalid IAM username: ${IAM_USER}" >&2
  exit $BAD_VALUE
fi

main
