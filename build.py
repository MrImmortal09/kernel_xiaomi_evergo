import argparse
import subprocess
import os
import shutil
import re
from datetime import datetime

debug_popen_impl = False

def popen_impl(command: list[str]):
    if debug_popen_impl:
        print('Execute command: "%s"...' % ' '.join(command), end=' ')
    s = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = s.communicate()
    out = out.decode("utf-8")
    err = err.decode("utf-8")
    if s.returncode != 0:
        if debug_popen_impl:
            print('failed')
        print("Command failed with error:\n", err)
        raise RuntimeError(f"Command failed: {command}. Exitcode: {s.returncode}")
    if debug_popen_impl:
        print(f'result: {s.returncode == 0}')
    return out.strip()

def check_file(filename):
    print(f"Checking file if exists: {filename}...", end=' ')
    exists = os.path.exists(filename)
    print("Found" if exists else "Not found")
    return exists

def match_and_get(regex: str, pattern: str):
    matched = re.search(regex, pattern)
    if not matched:
        raise AssertionError(f"Failed to match: {regex} in pattern: {pattern}")
    return matched.group(1)

class CompilerClang:
    @staticmethod
    def test_executable():
        try:
            popen_impl(['./toolchain/bin/clang', '-v'])
        except RuntimeError as e:
            print("Failed to execute clang. Ensure the toolchain is configured correctly.")
            raise e
    
    @staticmethod
    def get_version():
        clangversionRegex = r"(.*?clang version \d+(\.\d+)*).*"
        tcversion = popen_impl(['./toolchain/bin/clang', '-v'])
        return match_and_get(clangversionRegex, tcversion)
    
def main():
    parser = argparse.ArgumentParser(description="Build Kernel for Xiaomi Evergo")
    parser.add_argument('--target', type=str, required=True, help="Target device (e.g., evergo)")
    parser.add_argument('--allow-dirty', action='store_true', help="Allow dirty build (skip cleaning)")
    args = parser.parse_args()
    
    if args.target != 'evergo':
        print("Please specify a valid target: evergo")
        return
    
    if not check_file("toolchain/bin/clang"):
        print(f"Toolchain not found in {os.getcwd()}. Ensure the toolchain is correctly set up.")
        return
    
    CompilerClang.test_executable()
    
    # Print toolchain info
    toolchain_version = CompilerClang.get_version()
    print(f"Using toolchain: {toolchain_version}")
    
    # Set up environment
    tcPath = os.path.join(os.getcwd(), 'toolchain', 'bin')
    if tcPath not in os.environ['PATH'].split(os.pathsep):
        os.environ["PATH"] = tcPath + ':' + os.environ["PATH"]
    
    outDir = 'out'
    if os.path.exists(outDir) and not args.allow_dirty:
        print('Cleaning output directory...')
        shutil.rmtree(outDir)
    
    # Compile the kernel
    make_defconfig = ['make', 'O=out', 'ARCH=arm64', 'LLVM=1', f'-j{os.cpu_count()}']
    make_defconfig.append(f'{args.target}_defconfig')
    
    t = datetime.now()
    print('Running defconfig...')
    popen_impl(make_defconfig)
    
    print('Building kernel...')
    popen_impl(['make', 'O=out', 'ARCH=arm64', 'LLVM=1', f'-j{os.cpu_count()}'])
    t = datetime.now() - t
    
    # Check and output Image file
    image_path = os.path.join(outDir, 'arch', 'arm64', 'boot', 'Image')
    if not check_file(image_path):
        print("Kernel build failed. Check logs for details.")
        return
    
    print(f"Kernel build completed in {t.total_seconds()} seconds.")
    print(f"Image file generated: {image_path}")
    
if __name__ == '__main__':
    main()
