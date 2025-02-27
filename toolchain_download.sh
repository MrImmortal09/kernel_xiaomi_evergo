          mkdir -p toolchain
          cd toolchain
          echo 'Download antman and sync'
          bash <(curl -s "https://raw.githubusercontent.com/Neutron-Toolchains/antman/main/antman") --sync
          echo 'Patch for glibc'
          bash <(curl -s "https://raw.githubusercontent.com/Neutron-Toolchains/antman/main/antman") --patch=glibc
          echo 'Done'
