# ბუნდოვანი კანონი — Fuzzzy Law

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](#)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green)](#)
[![Build](https://img.shields.io/badge/build-passing-brightgreen)](#)

> AI-powered legal advocate for Georgian citizens.

**Fuzzzy Law** is an intelligent, case-centric legal assistant that puts the full weight of Georgian law—statutes, Supreme Court practice, and Grand Chamber decisions—into the hands of ordinary people. This is not just a legal search engine; it is an advocate that helps users compile facts, evaluate legal standing, and build strong legal cases based on 20,712 curated chunks of Georgian law.

## Core Features

- **Multi-Source RAG Pipeline**: Intelligent search across 12 legal codes, Supreme Court practices, and Grand Chamber decisions using Google Vertex AI `gemini-embedding-001`.
- **Case Builder**: Users can describe a situation, and the AI organizes the facts, identifies applicable laws, predicts outcomes, and structures a defense case.
- **Smart Conversations**: State-machine-driven chat that clarifies ambiguous details and provides targeted advice using Gemini 3.1 Pro.
- **Flutter Multi-Platform UI**: A responsive, 5-tab native application (Chat, Cases, Laws, Notes, Profile) with support for English and Georgian.
- **Credit & Tier System**: Configurable rate-limiting and credit gates (FREE/PRO/ADMIN) powered by Firebase Authentication.

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- 🚀 [Quick Start Guide](docs/QUICKSTART.md) — Get the project running locally in under 30 minutes.
- 🏗️ [Architecture](docs/ARCHITECTURE.md) — High-level system design, data flows, and database schema.
- 🔌 [API Reference](docs/API.md) — Complete specification of all REST and WebSocket endpoints.
- 👨‍💻 [Development Guide](docs/DEVELOPMENT.md) — Code style, testing, and contribution instructions.
- ⚖️ [Law Corpus](docs/LAW_CORPUS.md) — Details on the legal data sources, chunking, and embedding processes.

## Getting Started

Check out the [Quick Start Guide](docs/QUICKSTART.md) to set up your local development environment, including:
1. Cloning the repository.
2. Generating the law corpus.
3. Running the FastAPI backend with Docker.
4. Launching the Flutter mobile application.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
