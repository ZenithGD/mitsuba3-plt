# Create a directory where build products are stored
mkdir build
cd build
cmake -GNinja .. -DCMAKE_C_COMPILER=clang-13 -DCMAKE_CXX_COMPILER=clang++-13
ninja