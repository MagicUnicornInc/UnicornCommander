# KognitiveKompanion

A modern, versatile AI interface for KDE and other desktop environments, designed to provide a seamless interaction with various AI backends including OpenAI, Ollama, and AMD Ryzen AI hardware acceleration.

## Features

- **Multi-Backend Support**: 
  - OpenAI API integration (GPT-4o, GPT-3.5-Turbo, etc.)
  - Ollama backend for local models
  - AMD Ryzen AI hardware acceleration
- **Advanced UI**:
  - Collapsible sections for a clean interface
  - Conversation sidebar for managing chat history
  - Modern styling with KDE theming integration
  - System tray icon and floating window option
- **Context Features**:
  - Screen capture capability for visual context
  - Audio input support
  - RAG (Retrieval-Augmented Generation) toggle
- **Conversation Management**:
  - Save and load conversations
  - Export chat history

## Requirements

- Python 3.8+ (Python 3.12 recommended)
- PyQt5
- KDE Plasma 5 Desktop (optional, works on other desktops too)
- One of the following backends:
  - OpenAI API key
  - Ollama running locally
  - AMD Ryzen AI compatible hardware (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MagicUnicornInc/KognitiveKompanion.git
cd KognitiveKompanion
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application with your preferred backend:
```bash
# OpenAI backend
./run_openai_gui.sh

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
│   ├── rag/              # Retrieval-Augmented Generation
│   ├── system/           # System integration and optimization
│   └── utils/            # Utility functions
├── amd-ryzen-ai/         # AMD Ryzen AI integration
├── quark-integration/    # Quantization toolkit integration
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