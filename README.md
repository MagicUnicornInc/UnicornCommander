# UnicornCommander KDE AI Interface

A modern, versatile AI interface for KDE and other desktop environments, designed to provide a seamless interaction with various AI backends including OpenAI, Ollama, and AMD Ryzen AI hardware acceleration, with advanced memory features for contextual AI interactions.

## Features

- **Multi-Backend Support**: 
  - OpenAI API integration (GPT-4o-mini, GPT-3.5-Turbo, GPT-4o, etc.)
  - Ollama backend for local models (Llama 3, Mistral, Phi-3, etc.)
  - AMD Ryzen AI hardware acceleration via XDNA NPU
- **Advanced UI**:
  - Collapsible sections for a clean interface
  - Conversation sidebar for managing chat history
  - Modern styling with KDE theming integration
  - System tray icon and floating window option
- **Advanced Memory System**:
  - Short-term memory for conversation context
  - Long-term memory via vector database (Qdrant or ChromaDB)
  - Structured storage with PostgreSQL and Redis
  - RAG (Retrieval-Augmented Generation) for enhanced responses
- **Agent Capabilities**:
  - Specialized agent types for different tasks (Code, KDE Desktop, Data Analysis)
  - MCP integration for extended capabilities
  - Agent workspace for complex interactions
- **Conversation Management**:
  - Save and load conversations
  - Semantic search across conversation history
  - Export chat history

## Requirements

- Python 3.12+ recommended
- PyQt6 (for KDE Plasma 6)
- KDE Plasma 6.1+ (tested with 6.1.5)
- KDE Frameworks 6.0+ (tested with 6.6.0)
- Qt 6.6+ (tested with 6.6.2)
- Wayland display server
- One of the following backends:
  - OpenAI API key
  - Ollama running locally
  - AMD Ryzen AI compatible hardware (optional)

## Installation for Ubuntu 24.10 with KDE Plasma 6

1. Install system dependencies:
```bash
# Install PyQt6 and database dependencies
sudo apt update
sudo apt install -y python3-pyqt6 python3-pyqt6.qtwebengine python3-pip python3-venv
sudo apt install -y libqt6sql6-psql redis-server postgresql
```

2. Clone the repository:
```bash
git clone https://github.com/MagicUnicornInc/UnicornCommander.git
cd UnicornCommander
```

3. Set up Python environment:
```bash
# Create and activate virtual environment
python3 -m venv ~/unicorn-env
source ~/unicorn-env/bin/activate

# Install Python dependencies
cd KDE_AI_Interface
pip install -r requirements.txt
```

4. For AMD Ryzen AI hardware acceleration (if supported):
```bash
# Install ROCm and XDNA drivers
./install_rocm_24.10.sh

# Download and install AMD Ryzen AI models
python download_vitis_ep.py
```

5. Run the application with your preferred interface:
```bash
# Unified Interface (with memory features, multiple backends, and agent capabilities)
./run_unified_ai_gui.sh

# OpenAI-specific interface
./run_openai_gui.sh

# OpenAI interface with smart memory features
./run_smart_openai_gui.sh

# Ollama backend
./run_kde_ai_interface.py

# AMD Ryzen AI (if supported hardware is available)
./run_ryzen_ai_model.py
```

## Configuration

See [MULTI_BACKEND_GUIDE.md](MULTI_BACKEND_GUIDE.md) for detailed setup of different backends.

For AMD Ryzen AI specific setup, see [README_RYZEN_AI_SETUP.md](README_RYZEN_AI_SETUP.md).

## Project Structure

```
├── app_root/             # Core application code
│   ├── ui/               # UI components and widgets
│   ├── mcp/              # Model Control Protocol client
│   ├── config/           # Configuration management
│   │   ├── settings.py   # Application settings
│   │   └── backends.py   # Multi-backend management
│   ├── rag/              # Retrieval-Augmented Generation
│   │   ├── indexer.py    # Document indexing for vector databases
│   │   └── retriever.py  # Context retrieval system
│   ├── memory/           # Memory system
│   │   ├── memory_integration.py  # Memory integration interface
│   │   └── structured_storage.py  # PostgreSQL/Redis storage
│   ├── agents/           # Agent system
│   │   └── agent_manager.py  # Agent type management
│   ├── system/           # System integration and optimization
│   │   ├── gpu/          # GPU optimization utilities
│   │   └── xdna/         # XDNA NPU integration
│   └── utils/            # Utility functions
├── amd-ryzen-ai/         # AMD Ryzen AI integration
├── quark-integration/    # Quantization toolkit integration
├── unified_ai_gui.py     # Unified interface with all features
├── smart_openai_gui.py   # OpenAI interface with memory features
└── MCP-INTEGRATION-GUIDE.md  # MCP server documentation
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Project Status

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for the current development status and roadmap.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- KDE Community
- OpenAI and Ollama projects
- AMD for Ryzen AI support
- PyQt/Qt developers