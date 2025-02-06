# Create a directory where build products are stored
mkdir build -p
cd build
cmake -GNinja .. -DCMAKE_C_COMPILER=clang-13 -DCMAKE_CXX_COMPILER=clang++-13 # -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON
ninja -j 4