# Sales Agent System

A comprehensive automated sales agent system that handles lead interactions, product sales, phone calls, and payment processing.

## Components

### 1. Lead Interaction Agent (`lead_interaction_agent.py`)
Manages all lead communication and tracking:
- Lead database management
- Communication history
- Lead status tracking
- Conversation context management

### 2. Product Sales Agent (`product_sales_agent.py`)
Handles product presentations and sales:
- Product catalog management
- Sales pitch generation
- Pricing management
- Deal creation and tracking

### 3. Phone Call Agent (`phone_call_agent.py`)
Manages voice communication:
- Inbound call handling
- Outbound call initiation
- Call recording and transcription
- Call routing and escalation

### 4. Payment Processing Agent (`payment_agent.py`)
Handles payment operations:
- Payment method management
- Transaction processing
- Receipt generation
- Refund handling

## Architecture

```
agents/
├── README.md
├── base_agent.py                 # Base class for all agents
├── lead_interaction_agent.py
├── product_sales_agent.py
├── phone_call_agent.py
├── payment_agent.py
├── orchestrator.py              # Main orchestrator coordinating all agents
├── models/
│   ├── lead.py
│   ├── product.py
│   ├── transaction.py
│   └── call_record.py
├── services/
│   ├── twilio_service.py        # Phone call integration
│   ├── stripe_service.py        # Payment processing
│   ├── database_service.py      # Data persistence
│   └── notification_service.py  # Alerts and updates
└── config/
    ├── settings.py
    └── constants.py
```

## Features

### Lead Management
- Automatic lead capture and qualification
- Lead scoring and prioritization
- Conversation history tracking
- CRM integration

### Sales Capabilities
- Product recommendations
- Dynamic pricing
- Sales follow-up automation
- Win/loss tracking

### Phone Integration
- Twilio API integration
- Call recording
- Transcription and analysis
- IVR capabilities

### Payment Processing
- Stripe integration
- Multiple payment methods
- PCI compliance
- Fraud detection

## Quick Start

```python
from agents.orchestrator import SalesOrchestrator

# Initialize the orchestrator
orchestrator = SalesOrchestrator(config='config/settings.py')

# Process a lead
result = orchestrator.process_lead(
    phone="+1234567890",
    email="contact@example.com",
    name="John Doe"
)

# Handle a call
call_result = orchestrator.handle_incoming_call(
    caller_id="+1234567890"
)

# Process payment
payment = orchestrator.process_payment(
    lead_id="lead_123",
    amount=99.99,
    payment_method="card"
)
```

## Configuration

See `config/settings.py` for configuration options including:
- API keys and credentials
- Database connection strings
- Phone service settings
- Payment processor credentials

## Testing

```bash
pytest tests/
```

## Deployment

- Docker support included
- Environment variable configuration
- Logging and monitoring
