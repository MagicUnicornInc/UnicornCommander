# AMD AI Setup & Dependency Checklist

This document outlines the software components, versions, and resources required to ensure a computer is fully up-to-date for running AI workloads leveraging AMD’s iGPU, NPU, and Ryzen AI optimizations. The below checklist is based on our UnicornCommander documentation, subcomponent guides, and various AMD official resources.

---

## 1. AMD GPU Drivers

- **Purpose:** Provides desktop graphics & compute support for AMD’s iGPU.
- **Source:** AMD Official Support
- **Link:** [AMD Support](https://www.amd.com/en/support)
- **Notes:** Use the appropriate driver (AMDGPU or AMDGPU-Pro) suitable for your hardware. Always refer to the AMD release notes for the latest version.

## 2. AMD ROCm Platform

- **Purpose:** Enables GPU-accelerated compute for deep learning and AI workloads on AMD hardware.
- **Documentation & Downloads:**
  - [ROCm Documentation](https://rocmdocs.amd.com/en/latest/)
  - [ROCm GitHub Repository](https://github.com/RadeonOpenCompute/ROCm)
- **Versioning:** Installation scripts in UnicornCommander (e.g., `install_rocm_24.10.sh` in UnicornCommander and `install_rocm_24.04.sh` in KognitiveKompanion) highlight the importance of using a tested version.

## 3. AMD Ryzen AI / XDNA Optimizations

- **Purpose:** Provides acceleration and specific library support to enable advanced AI features on Ryzen platforms.
- **Source:** AMD Official Ryzen AI information
- **Link:** [AMD Ryzen AI](https://www.amd.com/en/technologies/ryzen-ai)
- **Versioning & Documentation:**
  - Refer to commit messages (e.g., commit `6343a85`) and installation scripts (`install_amd_ryzen_ai_stack.sh`) in UnicornCommander for version details and specific optimizations.

## 4. NPU Drivers and Firmware

- **Purpose:** Ensures the Neural Processing Unit (NPU) functions optimally by providing necessary drivers and firmware.
- **Source:** Typically bundled with AMD GPU driver packages or available through AMD’s developer resources.
- **Notes:** Consult your hardware documentation and AMD technical references for any additional firmware updates or patches.

## 5. Additional AI Framework Components and Installation Scripts

- **Examples in Our Setup:**
  - `install_vitis_ai.sh` (for Vitis AI-related dependencies)
  - Demo/test clients such as `ollama_test_client.py`, `openai_deepseek_gui.py`
- **Notes:** The versions of these scripts and instructions are documented in files like `README_RYZEN_AI_SETUP.md`, `MCP-QUICKSTART.md`, and `PROJECT_STATUS.md` in the UnicornCommander repository.

## 6. Overall System Documentation

- **Purpose:** Provides comprehensive guidelines for system setup and versioning across the entire UnicornCommander platform.
- **Key Documentation Files:**
  - `MCP-QUICKSTART.md`
  - `PROJECT_STATUS.md`
  - `INSTALL.md`
  - `README_RYZEN_AI_SETUP.md`
- **Notes:** Regularly review these files for updates as our system evolves.

---

## Summary

To fully support AMD’s AI optimizations, ensure that:

- **AMD GPU drivers** are current as per AMD’s official release notes.
- The **ROCm platform** is installed at the version recommended for your hardware (e.g., 24.10 or 24.04 as per our scripts).
- **Ryzen AI / XDNA libraries** are properly installed following our documentation.
- Necessary **NPU drivers/firmware** are in place (check AMD resources/documentation).
- All **supplementary installation scripts and configuration files** are synchronized with the version references provided in UnicornCommander documentation.

This checklist is intended to be a living document as new updates and improvements are made available.

