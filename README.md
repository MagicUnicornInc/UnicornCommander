# UnicornCommander

Welcome to UnicornCommander, the unified project repository for our advanced AI interface solutions. This repository consolidates multiple projects and components under one roof, while ensuring clear separation of concerns and avoiding duplication.

## Projects Included

1. **KDE AI Interface**
   - Contains the core frontend application. It uses API/dbus to communicate with backend services, enabling users to select the service they want to use.
   - Houses modules for configuration, UI, system utilities, and core client functionality.
   - Includes hardware-specific components such as AMD/Ryzen AI software files and drivers.

2. **MCP Servers**
   - Contains server-side components for MCP (Message/Control Protocol) communication.
   - Includes files such as `launch_mcp_servers.py`, integration guides, and quickstart documentation. This is the backend service that works with the KDE AI Interface.

3. **Quark Server**
   - Dedicated to the Quark server and its integration for AMD Ryzen AI hardware.
   - Contains the installation and integration scripts (located in the `quark-integration` and `quark_install` folders).
   - Serves as an independent backend service that the KDE AI Interface can communicate with via API/dbus.
   - **NEW**: Supports optimized DeepSeek models on Ryzen 9 8945HS with 780M iGPU and XDNA NPU acceleration.

## Documentation

Comprehensive documentation for the project can be found in the **Docs** folder, which includes:

- **Ollama_iGPU_Config.md** – Configuration and acceleration details for running Ollama on supported iGPU hardware.
- **Docker_Container_Instructions.md** – Guidelines for containerizing each service, including driver versions, compatibility notes, and transition details from Vitis AI to Quark.
- **RYZEN_AI_DeepSeek_Quark_Guide.md** – A complete guide on the recommended pipeline (Quark + ONNX + INT8 models) for AMD Ryzen AI, including key URLs and performance notes.

## Project Structure

- **KDE_AI_Interface/**: 
   - Contains the frontend application, demos, configuration files, and hardware-specific software.
   - Includes multiple backend support (OpenAI API, Ollama, AMD Ryzen AI)
   - Features advanced memory system and agent capabilities

- **MCP_Servers/**:
   - Contains backend components for MCP communication, including server launch scripts and documentation.
   - Provides context protocol for extended AI capabilities

- **Quark_Server/**:
   - Contains components related to the Quark server integration.
   - **NEW**: Enhanced with optimized DeepSeek models (1.3B and 6.7B)
   - **NEW**: Hardware acceleration support for Ryzen 9 8945HS with XDNA NPU
   - **NEW**: Automatic fallback to CPU when acceleration is unavailable

- **Docs/**:
   - Contains all detailed documentation regarding configuration, containerization instructions, and hardware compatibility guides.

## Hardware Acceleration

UnicornCommander now provides optimized support for AMD Ryzen AI hardware:

- **XDNA NPU Acceleration**: Utilize the Neural Processing Unit for efficient model inference
- **iGPU Acceleration**: Leverage the AMD 780M integrated GPU for parallel compute
- **Hybrid Execution**: Intelligently split workloads across NPU, GPU, and CPU
- **Model Quantization**: INT8/INT4 quantization for optimal performance
- **Performance Tuning**: System-level optimizations for maximum throughput

For detailed setup instructions, see the README in `Quark_Server/quark-integration/`.

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/MagicUnicornInc/UnicornCommander.git
   ```

2. Navigate to the project directory:
   ```bash
   cd UnicornCommander
   ```

3. Set up the Quark integration for AMD Ryzen AI hardware:
   ```bash
   cd Quark_Server/quark-integration
   ./setup_ryzen_ai.sh
   ./run_optimized_deepseek.sh
   ```

4. For other components, follow instructions in their respective README files.

## Performance Expectations

When properly configured on a Ryzen 9 8945HS:

- **DeepSeek 6.7B**: 15-25 tokens/second with NPU acceleration
- **DeepSeek 1.3B**: 40-60 tokens/second with NPU acceleration
- **CPU-only fallback**: Still functional with reduced performance

## Development Workflow

- Use GitHub Issues and Projects to track tasks and milestones for each component.
- Frontend development, backend server improvements, and documentation will progress in parallel.

## Contributing

Feel free to fork this repository, implement changes in individual components, and submit pull requests. Please refer to the contribution guidelines in each sub-directory for further instructions.

## License

This project is licensed under the terms specified in the LICENSE files for each component. Please refer to those files for additional details.

