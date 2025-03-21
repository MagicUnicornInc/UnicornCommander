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
   - Dedicated to the Quark server and its integration.
   - Contains the installation and integration scripts (located in the `quark-integration` and `quark_install` folders).
   - Serves as an independent backend service that the KDE AI Interface can communicate with via API/dbus.

## Documentation

Comprehensive documentation for the project can be found in the **Docs** folder, which includes:

- **Ollama_iGPU_Config.md** – Configuration and acceleration details for running Ollama on supported iGPU hardware.
- **Docker_Container_Instructions.md** – Guidelines for containerizing each service, including driver versions, compatibility notes, and transition details from Vitis AI to Quark.
- **RYZEN_AI_DeepSeek_Quark_Guide.md** – A complete guide on the recommended pipeline (Quark + ONNX + INT8 models) for AMD Ryzen AI, including key URLs and performance notes.

## Project Structure

- **KDE_AI_Interface/**: 
   - Contains the frontend application, demos, configuration files, and hardware-specific software.

- **MCP_Servers/**:
   - Contains backend components for MCP communication, including server launch scripts and documentation.

- **Quark_Server/**:
   - Contains components related to the Quark server integration.

- **Docs/**:
   - Contains all detailed documentation regarding configuration, containerization instructions, and hardware compatibility guides.

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/MagicUnicornInc/UnicornCommander.git
   ```

2. Navigate to the project directory:
   ```bash
   cd UnicornCommander
   ```

3. Follow instructions in the respective README files within each sub-directory for installation and setup.

## Development Workflow

- Use GitHub Issues and Projects to track tasks and milestones for each component.
- Frontend development, backend server improvements, and documentation will progress in parallel.

## Contributing

Feel free to fork this repository, implement changes in individual components, and submit pull requests. Please refer to the contribution guidelines in each sub-directory for further instructions.

## License

This project is licensed under the terms specified in the LICENSE files for each component. Please refer to those files for additional details.

