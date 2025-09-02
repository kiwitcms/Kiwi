# PTRAX - Software Test Management System

PTRAX is a fork of Kiwi TCMS customized for  to manage test cases, executions, and traceability. 
It allows flexible test metadata, tagging, and full traceability from requirements to test results.

## Features

- Unique Test Case IDs
- Flexible Tags & Custom Fields (JSON support)
- Test Plans and Executions
- Traceability Matrix: Requirements → Tests → Executions
- Search and Filter across multiple fields
- Export/Import via JSON and CSV
- Role-based Access Control (Admin, Test Manager, Tester, Observer)

## Quick Start

### Prerequisites
- Docker >= 20.x
- Docker Compose (optional for multi-container setup)
- Python 3.9+ (if running dev server)

### Running via Docker
```bash
docker build -t ???/PTRAX:latest .
docker run -d -p 8080:8080 ???/PTRAX:latest

## Contribution

- All development should be done in feature branches.
- Use `git pull` from upstream to merge Kiwi updates when needed.
- Docker image rebuild required after any changes.

## Future Plans

- UI modernization (React frontend)
- Enhanced traceability reports
- CI/CD integration for automated test execution
