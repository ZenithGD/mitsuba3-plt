include_directories(
  ${RGB2SPEC_INCLUDE_DIRS}
)

set(INC_DIR "../../include/mitsuba/plt")

add_library(mitsuba-plt OBJECT
  ${INC_DIR}/fwd.h

  plt.cpp                       ${INC_DIR}/plt.h
  bouncebuffer.cpp              ${INC_DIR}/bouncebuffer.h
#   diffractiongrating.cpp        ${INC_DIR}/diffractiongrating.h
)

target_compile_definitions(mitsuba-plt
  PRIVATE -DMI_BUILD_MODULE=MI_MODULE_LIB)

set_target_properties(mitsuba-plt PROPERTIES
  INTERPROCEDURAL_OPTIMIZATION ON)

set_target_properties(mitsuba-plt PROPERTIES
  POSITION_INDEPENDENT_CODE ON)

# Link to rgb2spec
target_link_libraries(mitsuba-plt PRIVATE rgb2spec)
target_link_libraries(mitsuba-plt PUBLIC drjit)

if (MI_ENABLE_JIT)
  target_link_libraries(mitsuba-plt PUBLIC drjit-core)
endif()

# Python bindings
if (MI_ENABLE_PYTHON)
  add_subdirectory(python)
  set(PLT_PY_V_SRC ${PLT_PY_V_SRC} PARENT_SCOPE)
  set(PLT_PY_SRC   ${PLT_PY_SRC}   PARENT_SCOPE)
endif()
