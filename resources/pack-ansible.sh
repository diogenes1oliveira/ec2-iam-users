#!/bin/bash

set -eo pipefail

PROGRAM_NAME="$0"
ROLE_NAME="ec2-iam-users"

FILES_TO_PACK="$(cat <<EOF
    roles/ec2-iam-users/defaults/
    roles/ec2-iam-users/files/
    roles/ec2-iam-users/meta/
    roles/ec2-iam-users/tasks/
    roles/ec2-iam-users/templates/
    roles/ec2-iam-users/vars/
    apply-ec2-iam-users-role.yml
    README.md
EOF
)"

usage() {
    cat <<EOF
Packs the contents of an Ansible directory into a ZIP file.

Usage:
    $PROGRAM_NAME [-q] [-d] [-o=<path>]

Parameters:
    -q, --quiet    quiet mode
    -d, --dry-run  takes no action, only shows the commands that would
                   be executed
    -o, --output   where to put the ZIP output (default: $OUTPUT_PATH)

Files to pack:
$FILES_TO_PACK
EOF
}

VERBOSE=true
DRY_RUN_PREFIX=''
OUTPUT_PATH="build/packed-role.zip"

main() {
    SCRIPT_DIR="$( dirname "$(realpath -ms "$BASH_SOURCE[0]")" )"
    ROOT_DIR="$( cd "$SCRIPT_DIR" && cd .. && pwd )"
    OUTPUT_PATH="$( realpath -ms "$OUTPUT_PATH" )"
    OUTPUT_DIR="$( dirname "$OUTPUT_PATH" )"
    TEMP_ZIP_PATH="$( uuidgen -r ).zip"

    show-info "Moving into the root directory $ROOT_DIR"
    $DRY_RUN_PREFIX cd "$ROOT_DIR"

    for FILE in $FILES_TO_PACK; do
        show-info "Adding $FILE to the temporary zipfile"

        if [[ "$FILE" == */ ]]; then
            FILE="$FILE*"
        fi

        $DRY_RUN_PREFIX zip -qr "$TEMP_ZIP_PATH" . -i "$FILE"
    done

    show-info "Assuring the output directory $OUTPUT_DIR exists"
    $DRY_RUN_PREFIX mkdir -p "$OUTPUT_DIR"

    show-info "Moving the temporary zipfile to $OUTPUT_PATH"
    $DRY_RUN_PREFIX mv "$TEMP_ZIP_PATH" "$OUTPUT_PATH"
}

show-info() {
    if [[ "$VERBOSE" == 'true' ]]; then
        echo "$@"
    fi
}

OPTS=$(getopt -o hqdo: --long help,quiet,dry-run,output: -- "$@")

if [[ "$?" != 0 ]]; then
    echo "Failed to parse args." >&2
    usage >&2
    exit 1
fi

eval set -- "$OPTS"

while true; do
    case "$1" in
        -h|--help )
            usage
            exit 0 ;;
        -q|--quiet )
            VERBOSE=false
            ;;
        -d|--dry-run )
            DRY_RUN_PREFIX="echo $ "
            ;;
        -o|--output )
            shift
            OUTPUT_PATH="$1"
            ;;
        --)
            shift
            break ;;
    esac
    shift
done

main
