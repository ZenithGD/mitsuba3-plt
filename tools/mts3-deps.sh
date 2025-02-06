# Install recent versions build tools, including Clang and libc++ (Clang's C++ library)
sudo apt install clang-13 libc++-13-dev libc++abi-13-dev cmake ninja-build

# Install libraries for image I/O
sudo apt install libpng-dev libjpeg-dev

# Install required Python packages
sudo apt install libpython3-dev python3-distutils

# For running tests
sudo apt install python3-pytest python3-pytest-xdist python3-numpy