# Luna Server Architecture Overview

## 🎯 System Vision

Luna Server is designed as a **modular, microservices-inspired backend** for AI-powered Vedic Astrology services. The system prioritizes:

- **Scalability**: Handle multiple messaging channels and high message volumes
- **Maintainability**: Clear separation of concerns and modular design
- **Extensibility**: Easy addition of new channels, services, and workflows
- **Reliability**: Robust error handling and graceful degradation
- **Performance**: Efficient message processing and resource utilization

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Channels                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────┐  │
│  │  WhatsApp   │  │  Telegram   │  │     Web     │  │ API  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Channel Integration Layer                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────┐  │
│  │  WhatsApp   │  │  Telegram   │  │     Web     │  │ API  │  │
│  │   Handler   │  │   Handler   │  │   Handler   │  │Handler│  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Core Services Layer                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Channels Service                               │ │
│  │  • User Management • Message Persistence • Channel Abstraction │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Router Service                                 │ │
│  │  • Intent Classification • Workflow Engine • Message Routing │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Domain Services Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────┐  │
│  │   Kundli    │  │Predictions  │  │     QnA     │  │Speech│  │
│  │  Services   │  │  Services   │  │  Services   │  │Services│  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Data Access Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────┐  │
│  │   Users     │  │  Profiles   │  │Conversations│  │Payments│ │
│  │     DAO     │  │     DAO     │  │     DAO     │  │   DAO  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Data Storage Layer                          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    PostgreSQL                               │ │
│  │  • User Data • Profiles • Conversations • Payments • etc.  │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Core Design Principles

### 1. **Separation of Concerns**
- **Channel Layer**: Handles platform-specific integrations
- **Service Layer**: Manages business logic and orchestration
- **Data Layer**: Handles data persistence and retrieval
- **Domain Layer**: Implements astrology-specific services

### 2. **Dependency Inversion**
- Services depend on abstractions (interfaces), not concrete implementations
- Easy to swap implementations (e.g., different LLM providers)
- Testable components with mock dependencies

### 3. **Single Responsibility**
- Each module has one clear purpose
- Services handle business logic, DAOs handle data access
- Clear boundaries between different concerns

### 4. **Open/Closed Principle**
- Open for extension (new channels, services, workflows)
- Closed for modification (existing functionality unchanged)
- Plugin-like architecture for new features

## 🚀 Key Architectural Components

### **Channel Integration Layer**
- **Purpose**: Abstract messaging platform differences
- **Components**: Platform-specific handlers (WhatsApp, Telegram, Web)
- **Benefits**: Unified message format, easy to add new platforms

### **Core Services Layer**
- **Channels Service**: User management, message persistence, channel abstraction
- **Router Service**: Intent classification, workflow orchestration, message routing
- **Benefits**: Centralized orchestration, consistent message processing

### **Workflow Engine**
- **Purpose**: Manage complex multi-step conversations
- **Features**: LLM integration, state management, error handling
- **Benefits**: Structured conversations, better user experience

### **Domain Services**
- **Kundli Services**: Astrology calculations and report generation
- **Predictions**: Horoscope and astrological insights
- **QnA Services**: General astrology questions and answers
- **Benefits**: Modular, testable, extensible domain logic

### **Data Access Layer**
- **Purpose**: Abstract database operations
- **Pattern**: Data Access Objects (DAOs) with synchronous operations
- **Benefits**: Consistent data access, easy to test and mock

## 🔄 Message Processing Flow

### **1. Message Reception**
```
External Message → Channel Handler → Canonical Format → Channels Service
```

### **2. Core Processing**
```
Channels Service → Router Service → Intent Classification → Workflow/Handler Selection
```

### **3. Business Logic**
```
Workflow Engine → Domain Services → Business Logic → Response Generation
```

### **4. Response Delivery**
```
Response → Channels Service → Channel Handler → External Platform
```

## 🎯 System Characteristics

### **Scalability**
- **Horizontal Scaling**: Stateless services can be replicated
- **Async Processing**: Non-blocking message handling
- **Connection Pooling**: Efficient database connection management
- **Caching**: Session and response caching strategies

### **Reliability**
- **Error Handling**: Comprehensive error recovery mechanisms
- **Fallback Strategies**: Graceful degradation on failures
- **Monitoring**: Real-time system health monitoring
- **Logging**: Structured logging for debugging and analysis

### **Security**
- **Input Validation**: Comprehensive input sanitization
- **Authentication**: User identity verification
- **Rate Limiting**: Protection against abuse
- **Data Privacy**: Secure handling of sensitive information

### **Maintainability**
- **Modular Design**: Clear component boundaries
- **Configuration-Driven**: Settings-based behavior control
- **Testing**: Comprehensive test coverage
- **Documentation**: Detailed technical documentation

## 🏗️ Current Architecture State

Luna Server currently operates as a modular monolithic backend with:
- Workflow engine for complex conversations
- Multi-channel support with unified interface
- Clear separation of concerns across layers

## 📊 Technology Stack

### **Backend Framework**
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLModel**: SQL databases in Python, designed for simplicity
- **PostgreSQL**: Robust, open-source relational database

### **AI & ML**
- **Custom LLM Client**: Unified interface for LLM providers with fallback support
- **OpenAI**: Primary LLM provider with GPT models
- **Custom Prompts**: Domain-specific prompt engineering

### **Infrastructure**
- **Docker**: Containerization for consistent deployment
- **AsyncIO**: Asynchronous programming for high performance

### **Monitoring & Observability**
- **Loguru**: Structured logging with JSON formatting
- **Custom Telemetry**: Application-specific metrics collection
- **Health Checks**: System health monitoring endpoints

---

This architecture provides a solid foundation for Luna Server's current needs while maintaining the flexibility to evolve into a more distributed, cloud-native system as requirements grow.
