#
# Master OpenCog Central CMake file.
#
# This file orchestrates the build of all OpenCog components in proper
# dependency order to ensure stable, correct operation.
#
# General organization:
# -- check for different compilers, OS'es
# -- search for various required & optional libraries/tools
# -- decide what to build based on above results.
# -- configure various config files.
# -- build components in dependency order
# -- print pretty summary
#

# CMake version requirement aligned with cogutil and atomspace
CMAKE_MINIMUM_REQUIRED(VERSION 3.16)

IF (COMMAND CMAKE_POLICY)
	CMAKE_POLICY(SET CMP0003 NEW)
ENDIF (COMMAND CMAKE_POLICY)

IF(CMAKE_VERSION VERSION_GREATER 3.0.2)
	CMAKE_POLICY(SET CMP0037 OLD)
ENDIF(CMAKE_VERSION VERSION_GREATER 3.0.2)

PROJECT(opencog-central)

# ----------------------------------------------------------
# User-modifiable options. Feel free to change these!
#
# uncomment to be in Release mode [default]
# SET(CMAKE_BUILD_TYPE Release)

# uncomment to build in debug mode
# SET(CMAKE_BUILD_TYPE Debug)

# uncomment to be in coverage testing mode
# SET(CMAKE_BUILD_TYPE Coverage)

# uncomment to build in profile mode
# SET(CMAKE_BUILD_TYPE Profile)

# uncomment to build in release mode with debug information
# SET(CMAKE_BUILD_TYPE RelWithDebInfo)

# default build type
IF (CMAKE_BUILD_TYPE STREQUAL "")
	SET(CMAKE_BUILD_TYPE Release)
ENDIF (CMAKE_BUILD_TYPE STREQUAL "")

MESSAGE(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

ADD_DEFINITIONS(-DPROJECT_SOURCE_DIR="${CMAKE_SOURCE_DIR}"
                -DPROJECT_BINARY_DIR="${CMAKE_BINARY_DIR}")

# ===============================================================
# OpenCog Central Components Build Order
#
# Components are built in dependency order to ensure proper installation
# 1. cogutil - base utilities for all OpenCog components
# 2. orc-as - AtomSpace orchestration (all atomspace components)
# 3. ure - Unified Rule Engine
# 4. attention - Attention allocation system
# 5. spacetime - Spatiotemporal reasoning
# 6. cogserver - Core server infrastructure
# 7. pln - Probabilistic Logic Networks
# 8. miner - Pattern mining
# 9. moses - Meta-Optimizing Semantic Evolutionary Search
# 10. asmoses - AtomSpace MOSES integration
# 11. learn - Learning systems
# 12. opencog - Main OpenCog framework
# 13. unify - Unification system
# 14. generate - Generation system
# 15. Optional components (vision, cheminformatics, etc.)

MESSAGE(STATUS "Building OpenCog Central - all components")

# ===============================================================
# Foundation Layer: Hardware Matrix & Tensor Configuration
# ===============================================================

# Include foundation layer hardware matrix configuration
INCLUDE(cmake/HardwareMatrix.cmake)

# Core foundation - Required
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/orc-dv/cogutil/CMakeLists.txt")
    MESSAGE(STATUS "Adding cogutil (foundation layer core utilities)")
    ADD_SUBDIRECTORY(orc-dv/cogutil)
    SET(HAVE_COGUTIL ON)
ELSE()
    MESSAGE(WARNING "cogutil not found in orc-dv - this is required!")
ENDIF()

# Foundation layer external tools
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/orc-dv/external-tools/CMakeLists.txt")
    MESSAGE(STATUS "Adding external-tools (foundation layer)")
    ADD_SUBDIRECTORY(orc-dv/external-tools)
ENDIF()

# Foundation layer MOSES (from orc-ai)
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/orc-ai/moses/CMakeLists.txt")
    MESSAGE(STATUS "Adding moses (foundation layer evolutionary algorithms)")
    ADD_SUBDIRECTORY(orc-ai/moses)
ENDIF()

# Advanced layer: Pattern Mining (from orc-ai)
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/orc-ai/miner/CMakeLists.txt")
    MESSAGE(STATUS "Adding miner (advanced layer pattern mining)")
    ADD_SUBDIRECTORY(orc-ai/miner)
ENDIF()

# Advanced layer: Probabilistic Logic Networks (from orc-ai)
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/orc-ai/pln/CMakeLists.txt")
    MESSAGE(STATUS "Adding pln (advanced layer probabilistic reasoning)")
    ADD_SUBDIRECTORY(orc-ai/pln)
ENDIF()

# Advanced layer: AtomSpace MOSES integration (from orc-ai)
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/orc-ai/asmoses/CMakeLists.txt")
    MESSAGE(STATUS "Adding asmoses (advanced layer AtomSpace MOSES)")
    ADD_SUBDIRECTORY(orc-ai/asmoses)
ENDIF()

# Advanced layer: Unified Rule Engine (from orc-ai)
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/orc-ai/ure/CMakeLists.txt")
    MESSAGE(STATUS "Adding ure (advanced layer unified reasoning)")
    ADD_SUBDIRECTORY(orc-ai/ure)
ENDIF()

# AtomSpace orchestration - Core infrastructure
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/orc-as/CMakeLists.txt")
    MESSAGE(STATUS "Adding orc-as (AtomSpace orchestration)")
    ADD_SUBDIRECTORY(orc-as)
ELSE()
    MESSAGE(WARNING "orc-as not found - AtomSpace components required!")
ENDIF()

# Unified Rule Engine - Core reasoning
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/ure/CMakeLists.txt")
    MESSAGE(STATUS "Adding ure (Unified Rule Engine)")
    ADD_SUBDIRECTORY(ure)
ENDIF()

# Attention system
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/attention/CMakeLists.txt")
    MESSAGE(STATUS "Adding attention (attention allocation)")
    ADD_SUBDIRECTORY(attention)
ENDIF()

# SpaceTime reasoning
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/spacetime/CMakeLists.txt")
    MESSAGE(STATUS "Adding spacetime (spatiotemporal reasoning)")
    ADD_SUBDIRECTORY(spacetime)
ENDIF()

# CogServer - Core server infrastructure
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/cogserver/CMakeLists.txt")
    MESSAGE(STATUS "Adding cogserver (server infrastructure)")
    ADD_SUBDIRECTORY(cogserver)
ENDIF()

# PLN - Probabilistic Logic Networks
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/pln/CMakeLists.txt")
    MESSAGE(STATUS "Adding pln (Probabilistic Logic Networks)")
    ADD_SUBDIRECTORY(pln)
ENDIF()

# Pattern Miner
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/miner/CMakeLists.txt")
    MESSAGE(STATUS "Adding miner (pattern mining)")
    ADD_SUBDIRECTORY(miner)
ENDIF()

# MOSES - Meta-Optimizing Semantic Evolutionary Search
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/moses/CMakeLists.txt")
    MESSAGE(STATUS "Adding moses (evolutionary search)")
    ADD_SUBDIRECTORY(moses)
ENDIF()

# AS-MOSES - AtomSpace MOSES integration
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/asmoses/CMakeLists.txt")
    MESSAGE(STATUS "Adding asmoses (AtomSpace MOSES)")
    ADD_SUBDIRECTORY(asmoses)
ENDIF()

# Learning system
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/learn/CMakeLists.txt")
    MESSAGE(STATUS "Adding learn (learning systems)")
    ADD_SUBDIRECTORY(learn)
ENDIF()

# Main OpenCog framework
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/opencog/CMakeLists.txt")
    MESSAGE(STATUS "Adding opencog (main framework)")
    ADD_SUBDIRECTORY(opencog)
ENDIF()

# Unification system
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/unify/CMakeLists.txt")
    MESSAGE(STATUS "Adding unify (unification system)")
    ADD_SUBDIRECTORY(unify)
ENDIF()

# Generation system
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/generate/CMakeLists.txt")
    MESSAGE(STATUS "Adding generate (generation system)")
    ADD_SUBDIRECTORY(generate)
ENDIF()

# Optional specialized components
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/vision/CMakeLists.txt")
    MESSAGE(STATUS "Adding vision (computer vision)")
    ADD_SUBDIRECTORY(vision)
ENDIF()

IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/cheminformatics/CMakeLists.txt")
    MESSAGE(STATUS "Adding cheminformatics (chemical informatics)")
    ADD_SUBDIRECTORY(cheminformatics)
ENDIF()

IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/lg-atomese/CMakeLists.txt")
    MESSAGE(STATUS "Adding lg-atomese (Link Grammar AtomESE)")
    ADD_SUBDIRECTORY(lg-atomese)
ENDIF()

IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/sensory/CMakeLists.txt")
    MESSAGE(STATUS "Adding sensory (sensory processing)")
    ADD_SUBDIRECTORY(sensory)
ENDIF()

# Robotics Embodied Cognition Layer
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/robotics-embodied/CMakeLists.txt")
    MESSAGE(STATUS "Adding robotics-embodied (embodied cognition layer)")
    ADD_SUBDIRECTORY(robotics-embodied)
ENDIF()

# GnuCash Cognitive Accounting Engine
IF(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/gnucashcog-v3/CMakeLists.txt")
    MESSAGE(STATUS "Adding gnucashcog-v3 (cognitive accounting engine)")
    ADD_SUBDIRECTORY(gnucashcog-v3)
ENDIF()

# ===================================================================
# CPack Configuration for Package Generation
# ===================================================================

# CPack meta-information
SET(CPACK_PACKAGE_NAME "cogml")
SET(CPACK_PACKAGE_VERSION "1.0.0")
SET(CPACK_PACKAGE_VENDOR "OpenCog Foundation")
SET(CPACK_PACKAGE_DESCRIPTION_SUMMARY "CogML - Cognitive Machine Learning Framework")
SET(CPACK_PACKAGE_DESCRIPTION_FILE "${CMAKE_CURRENT_SOURCE_DIR}/README.md")
SET(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
SET(CPACK_PACKAGE_CONTACT "cogml-dev@opencog.org")

# Package generators - supporting multiple formats as requested
SET(CPACK_GENERATOR "TGZ;ZIP")

# Debian package specific settings
IF(UNIX AND NOT APPLE)
    LIST(APPEND CPACK_GENERATOR "DEB")
    SET(CPACK_DEBIAN_PACKAGE_MAINTAINER "OpenCog Foundation")
    SET(CPACK_DEBIAN_PACKAGE_SECTION "science")
    SET(CPACK_DEBIAN_PACKAGE_PRIORITY "optional")
    SET(CPACK_DEBIAN_PACKAGE_DEPENDS "libboost-all-dev (>= 1.60), cmake (>= 3.16)")
ENDIF()

# Source package configuration
SET(CPACK_SOURCE_GENERATOR "TGZ;ZIP")
SET(CPACK_SOURCE_IGNORE_FILES
    "/\\\\.git/"
    "/build/"
    "/\\\\.gitignore"
    "/\\\\.github/"
    "\\\\.swp$"
    "\\\\.orig$"
    "/CMakeLists\\\\.txt\\\\.user"
    "/private/"
)

# Component-based packaging for modular installation
SET(CPACK_COMPONENTS_ALL foundation core ai robotics web docs)

# Foundation layer components  
SET(CPACK_COMPONENT_FOUNDATION_DISPLAY_NAME "Foundation Layer")
SET(CPACK_COMPONENT_FOUNDATION_DESCRIPTION "Core utilities and base OpenCog infrastructure")
SET(CPACK_COMPONENT_FOUNDATION_GROUP "Base")

# Core layer components
SET(CPACK_COMPONENT_CORE_DISPLAY_NAME "Core Layer") 
SET(CPACK_COMPONENT_CORE_DESCRIPTION "AtomSpace and core reasoning components")
SET(CPACK_COMPONENT_CORE_GROUP "Base")
SET(CPACK_COMPONENT_CORE_DEPENDS foundation)

# AI layer components
SET(CPACK_COMPONENT_AI_DISPLAY_NAME "AI Layer")
SET(CPACK_COMPONENT_AI_DESCRIPTION "Learning, reasoning, and evolutionary algorithms")
SET(CPACK_COMPONENT_AI_GROUP "Intelligence")
SET(CPACK_COMPONENT_AI_DEPENDS core)

# Robotics components
SET(CPACK_COMPONENT_ROBOTICS_DISPLAY_NAME "Robotics Layer")
SET(CPACK_COMPONENT_ROBOTICS_DESCRIPTION "Embodied cognition and robotics integration")
SET(CPACK_COMPONENT_ROBOTICS_GROUP "Applications")
SET(CPACK_COMPONENT_ROBOTICS_DEPENDS ai)

# Web components
SET(CPACK_COMPONENT_WEB_DISPLAY_NAME "Web Layer")
SET(CPACK_COMPONENT_WEB_DESCRIPTION "RESTful APIs and web interfaces")
SET(CPACK_COMPONENT_WEB_GROUP "Applications") 
SET(CPACK_COMPONENT_WEB_DEPENDS core)

# Documentation
SET(CPACK_COMPONENT_DOCS_DISPLAY_NAME "Documentation")
SET(CPACK_COMPONENT_DOCS_DESCRIPTION "API documentation and user guides")
SET(CPACK_COMPONENT_DOCS_GROUP "Documentation")

# Component groups
SET(CPACK_COMPONENT_GROUP_BASE_DESCRIPTION "Essential OpenCog components")
SET(CPACK_COMPONENT_GROUP_INTELLIGENCE_DESCRIPTION "AI and learning components")
SET(CPACK_COMPONENT_GROUP_APPLICATIONS_DESCRIPTION "Application-specific components")
SET(CPACK_COMPONENT_GROUP_DOCUMENTATION_DESCRIPTION "Documentation and examples")

# Include CPack module to enable packaging
INCLUDE(CPack)

# ===================================================================
# Show a summary of what was built

MESSAGE(STATUS "")
MESSAGE(STATUS "========================================")
MESSAGE(STATUS "OpenCog Central Build Summary")
MESSAGE(STATUS "========================================")
MESSAGE(STATUS "All available OpenCog components have been configured.")
MESSAGE(STATUS "Components will be built in dependency order.")
MESSAGE(STATUS "Use 'make' to build all components.")
MESSAGE(STATUS "Use 'make install' to install all components.")
MESSAGE(STATUS "Use 'cpack' to generate distribution packages.")
MESSAGE(STATUS "========================================")
MESSAGE(STATUS "")