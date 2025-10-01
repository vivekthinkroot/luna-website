# Luna Backend

Luna is an AI-powered Vedic Astrology assistant designed for messaging platforms (WhatsApp, Telegram, Web) with voice and text capabilities.

## 🚀 Quick Start

- **[Installation Guide](docs/getting-started/installation.md)** - Get Luna Server running on your system
- **[Configuration](docs/getting-started/configuration.md)** - Set up environment variables and settings
- **[Settings Guide](docs/settings-guide.md)** - Comprehensive configuration options and environment variables
- **[Quick Start Tutorial](docs/getting-started/quick-start.md)** - Build your first integration in minutes

## 📚 Documentation

**📖 [Full Documentation](docs/README.md)** - Comprehensive project documentation

### **Key Sections:**
- **[Architecture Overview](docs/architecture/overview.md)** - System design and architecture
- **[System Design](docs/architecture/system-design.md)** - Detailed technical implementation
- **[Data Flow](docs/architecture/data-flow.md)** - Message processing and system flows
- **[Deployment](docs/architecture/deployment.md)** - Production deployment strategies

### **Guides:**
- **[Intent Management](docs/guides/intent-management.md)** - Understanding and managing user intents
- **[Workflow Development](docs/guides/workflow-development.md)** - Creating custom conversation workflows
- **[Channel Integration](docs/guides/channel-integration.md)** - Adding new messaging platforms

## 🏗️ Project Overview

This repository contains the backend services for Luna, built with FastAPI, SQLModel, and a modular microservices-inspired architecture. The system is designed for scalability, maintainability, and easy integration with multiple messaging channels.

## ✨ Key Features

- **Modular, microservices-inspired Python backend**
- **FastAPI for API and webhook handling**
- **SQLModel + PostgreSQL for data storage**
- **Loguru-based structured logging**
- **LLM integration via LiteLLM**
- **Voice and text support**
- **Provider-agnostic integrations**
- **Advanced workflow engine for complex conversations**
- **Multi-channel support (WhatsApp, Telegram, Web)**

## 🚀 Setup Instructions

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Configure environment variables**:
   - Copy `.env.example` to `.env` and fill in required values
4. **Run the application**:
   ```bash
   uvicorn api.app:app --reload
   ```

## 🏗️ Architecture

- **api/**: FastAPI app and webhook endpoints
- **channels/**: Handlers for Telegram, WhatsApp, Web, etc.
- **services/**: Core business logic, speech, routing, and workflow engine
- **kundli/**, **predictions/**, **qna/**: Domain services
- **data/**: Database models and connection
- **dao/**: Data access objects (CRUD)
- **utils/**: Logging, LLM, telemetry, sessions
- **config/**: Pydantic-based settings
- **artifacts/**: PDF/image generation templates
- **tests/**: Unit and integration tests

## 🔧 Development

### **Adding New Features**
- **[Intent Management Guide](docs/guides/intent-management.md)** - Add new user intents
- **[Workflow Development Guide](docs/guides/workflow-development.md)** - Create custom workflows
- **[Channel Integration Guide](docs/guides/channel-integration.md)** - Add new messaging platforms

### **Testing**
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/ -k "workflow" # Tests with "workflow" in name
```

### **Code Quality**
- Follow PEP 8 style guidelines
- Use type hints throughout
- Write comprehensive tests for new features
- Update documentation for API changes

## 📊 Project Status

- **Current Version**: 1.0.0
- **Status**: Production Ready
- **Last Updated**: December 2024
- **Maintainers**: Luna Development Team

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/README.md](docs/README.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/luna-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/luna-server/discussions)

---

**Note**: For comprehensive documentation, architecture details, and development guides, see the [full documentation](docs/README.md).
