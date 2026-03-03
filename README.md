# message2

<div align="center">
  <img src="docs/logo.svg" alt="message2 logo" width="200"/>
</div>

Client-server messaging platform with a focus on security, flexibility, and extensibility.

## Purpose

message2 is a secure messaging system demonstrating modern client-server architecture, real-time communication, and multimedia support.
It aims to provide a foundation for a production-ready messaging platform capable of deployment in both corporate and public environments.

## Features (in development)

* Real-time text messaging (WebSocket)
* File and multimedia sharing
* Voice messages
* Private and group chats
* Contact management
* Configurable security policies
* Support for deployment in corporate and public networks

## Technology Stack

* **Backend:** Python, FastAPI
* **Frontend:** React, TypeScript
* **Databases:** PostgreSQL, Redis
* **Object Storage:** MinIO (S3-compatible)
* **Infrastructure:** Docker, Nginx

## Project Structure

```text
message2/
├── backend/   # server-side application
├── docker/    # Docker configurations
├── docs/      # documentation and assets
├── frontend/  # web client
├── .gitignore
├── LICENSE
└── README.md
```

## Security & Compliance

The platform is designed with security in mind:

* Authentication and authorization via JWT
* Optional end-to-end encryption
* Configurable security policies
* Support for corporate deployment scenarios

## Status

Active development. Features are subject to change.

## License

MIT

---
