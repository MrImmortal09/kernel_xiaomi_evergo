#!/bin/bash

# Function for executing commands with log generation
popen_impl() {
    local pid=$$
    local stdout_log="${pid}_stdout.log"
    local stderr_log="${pid}_stderr.log"

    # Execute the command and capture output
    "$@" 1> "$stdout_log" 2> "$stderr_log"
    exit_code=$?

    # Print log file names
    echo "Output log files: $stdout_log, $stderr_log"

    if [[ $exit_code -ne 0 ]]; then
        echo "Command failed: $*. Exitcode: $exit_code"
        exit 1
    fi
}

# Function to check if a file exists
check_file() {
    local filename="$1"
    echo "Checking file if exists: $filename..." -n
    if [[ -f "$filename" ]]; then
        echo "Found"
        return 0
    else
        echo "Not found"
        return 1
    fi
}

# Parse command-line arguments
TARGET=""
ALLOW_DIRTY=0
TOOLCHAIN_PATH="./toolchain/bin"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --target) TARGET="$2"; shift ;;
        --allow-dirty) ALLOW_DIRTY=1 ;;
        --toolchain-path) TOOLCHAIN_PATH="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Validate target
if [[ "$TARGET" != "evergo" ]]; then
    echo "Please specify a valid target: evergo"
    exit 1
fi

# Add toolchain to PATH
TOOLCHAIN_BIN_PATH="$TOOLCHAIN_PATH/bin"
export PATH="$TOOLCHAIN_BIN_PATH:$PATH"

# Output directory
OUT_DIR="out"

# Clean output directory if not allowing dirty build
if [[ -d "$OUT_DIR" ]] && [[ $ALLOW_DIRTY -eq 0 ]]; then
    echo "Cleaning output directory..."
    rm -rf "$OUT_DIR"
fi

# Start timing
start_time=$(date +%s)

# Run defconfig
echo "Running defconfig..."
popen_impl make O="$OUT_DIR" ARCH=arm64 LLVM=1 -j"$(nproc)" "${TARGET}_defconfig"

# Build kernel
echo "Building kernel..."
popen_impl make O="$OUT_DIR" ARCH=arm64 LLVM=1 -j"$(nproc)"

# Calculate build time
end_time=$(date +%s)
build_time=$((end_time - start_time))

# Check Image file
IMAGE_PATH="$OUT_DIR/arch/arm64/boot/Image"
if ! check_file "$IMAGE_PATH"; then
    echo "Kernel build failed. Check logs for details."
    exit 1
fi

# Print completion message
echo "Kernel build completed in $build_time seconds."
echo "Image file generated: $IMAGE_PATH"