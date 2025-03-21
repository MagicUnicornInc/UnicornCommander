# KognitiveKompanion

Welcome to KognitiveKompanion, the unified project repository for our advanced AI interface solutions. This repository consolidates multiple projects and components while avoiding duplication and ensuring clarity in separation of concerns.

## Projects Included

1. **KDE AI Interface**
   - Contains the core frontend application. It uses API/dbus to communicate with backend services, enabling users to select the service they want to use.
   - Houses modules for configuration, UI, system utilities, and core client functionality.
   - Hardware-specific components such as AMD/Ryzen AI Software files and drivers are included.

2. **MCP Servers**
   - Contains server-side components for MCP (Message/Control Protocol) communication.
   - Includes files such as `launch_mcp_servers.py`, integration guides, and quickstart documentation. This is the backend service that works with the KDE AI Interface.

3. **Quark Server**
   - Dedicated to the Quark server and its integration.
   - Contains the `quark-integration` and `quark_install` folders.
   - Serves as an independent backend service that the KDE AI Interface can communicate with via API/dbus.

## Project Structure

- **KDE_AI_Interface/**: 
   - Core frontend application, demos, configuration, and hardware-specific software for AMD/Ryzen.
   - Uses modular components located in `app_root/` and various demo scripts for GUI interactions.

- **MCP_Servers/**:
   - Server-side components for MCP communication.
   - Includes server launch scripts and integration documentation.

- **Quark_Server/**:
   - Dedicated Quark server integration.
   - Contains the installation and integration scripts in `quark-integration/` and `quark_install/`.

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/MagicUnicornInc/KognitiveKompanion.git
   ```

2. Navigate to the project directory:
   ```bash
   cd KognitiveKompanion
   ```

3. Follow instructions in the respective README files in each sub-directory for installation and setup.

## Development Workflow

- Use GitHub Issues and Projects to track tasks and milestones for each component.
- Separate development streams for frontend (KDE_AI_Interface) and backend (MCP_Servers and Quark_Server) to ensure clarity in responsibilities.

## Contributing

Feel free to fork this repository, work on individual components, and submit pull requests. Please refer to the guidelines in each sub-directory for further instructions.

## License

This project is licensed under the terms specified in the LICENSE files in each component. Please refer to those files for details.

