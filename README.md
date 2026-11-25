# OTP Mail Service

A FastAPI microservice for sending OTP emails using RabbitMQ and Resend.

## Features

- ✅ Asynchronous email sending using Resend API
- ✅ RabbitMQ message queue consumption
- ✅ Automatic reconnection with exponential backoff
- ✅ Health check endpoint
- ✅ Graceful shutdown handling
- ✅ Structured logging
- ✅ Environment-based configuration
- ✅ Type hints and Pydantic validation

## Prerequisites

- Python 3.11+
- RabbitMQ server
- Resend API account and API key

## 📦 Installation & Setup

### 1. Clone and Setup Project

```bash
# Clone your project or navigate to project directory
cd otp-mail-service

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Run Project
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000