# Order Management System (OMS)

A RESTful API service for managing e-commerce orders built with FastAPI and MongoDB.

## Overview

The Order Management System provides a complete backend solution for handling customer orders in an e-commerce environment. It features JWT-based authentication, role-based authorization, and comprehensive CRUD operations for order management.

## Core Functionality

### Order Management
- **Create Orders**: Customers can create new orders with multiple items
- **View Orders**: Users can view their own orders, admins can view all orders
- **Update Orders**: Admin-only functionality for order status management
- **Delete Orders**: Admin-only functionality for order removal
- **Order Listing**: Paginated order listing with status filtering

### Authentication & Authorization
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access**: Customer and admin role separation
- **User Isolation**: Customers can only access their own orders

### Data Validation
- **Input Validation**: Comprehensive validation for all order fields
- **Price Validation**: Positive price enforcement with decimal precision
- **Quantity Validation**: Positive quantity requirements
- **Status Management**: Controlled order status transitions

### Order Status Flow
- **Pending** → **Processing** → **Shipped** → **Delivered**
- **Cancellation**: Orders can be cancelled at any stage
- **Admin Control**: Only admins can modify order status

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/` | API status | No |
| `GET` | `/health` | Health check | No |
| `POST` | `/orders` | Create order | Customer/Admin |
| `GET` | `/orders/{id}` | Get order by ID | Customer/Admin |
| `GET` | `/orders` | List orders | Customer/Admin |
| `PATCH` | `/orders/{id}` | Update order | Admin only |
| `DELETE` | `/orders/{id}` | Delete order | Admin only |

## Technology Stack

- **FastAPI**: Modern Python web framework
- **MongoDB**: Document database with Motor async driver
- **JWT**: JSON Web Tokens for authentication
- **Pydantic**: Data validation and serialization
- **Docker**: Containerized deployment

## Application Structure

```
app/
├── main.py              # FastAPI application and API endpoints
├── models.py            # Pydantic models for data validation
├── auth.py              # JWT authentication and authorization
└── database.py          # MongoDB connection and configuration
```

### File Descriptions

- **main.py**: Contains the FastAPI application instance and all API route handlers (CRUD operations)
- **models.py**: Defines Pydantic models for request/response validation (OrderCreate, OrderUpdate, OrderResponse)
- **auth.py**: Implements JWT token creation, verification, and user authentication dependencies
- **database.py**: Manages MongoDB connection using Motor async driver and database configuration

## API Test Automation

### Test Framework Architecture

The project implements comprehensive API test automation using:

- **pytest**: Primary testing framework
- **requests**: HTTP client for API testing
- **MongoDB**: Isolated test databases
- **Docker Compose**: Containerized test environment

### Test Organization

```
tests/
├── conftest.py              # Test fixtures and configuration
└── unit/
    ├── test_orders_crud_create.py    # Order creation tests
    ├── test_orders_crud_read.py      # Order retrieval tests
    ├── test_orders_crud_update.py    # Order update tests
    └── test_orders_crud_delete.py    # Order deletion tests
```

### Test Categories

#### CRUD Operations (`@pytest.mark.crud`)
- **Create**: Order creation with validation
- **Read**: Order retrieval and listing
- **Update**: Order status modifications
- **Delete**: Order removal operations

#### Authentication Tests (`@pytest.mark.auth`)
- JWT token validation
- Role-based access control
- Unauthorized access prevention

#### Validation Tests (`@pytest.mark.validation`)
- Input field validation
- Price and quantity constraints
- Status transition rules

### Parallel Test Execution

The test suite supports parallel execution using `pytest-xdist`:

```bash
# Run tests in parallel across multiple workers
pytest -n auto

# Run specific test categories
pytest -m "crud and create"
pytest -m "auth"
pytest -m "validation"
```

### Test Database Isolation

Each test uses isolated MongoDB databases to prevent interference:

- **Unique databases per test**: Prevents data contamination
- **Automatic cleanup**: Databases are dropped after test completion
- **Parallel safety**: Multiple workers can run simultaneously

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+

### Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd order_management_system_python
```

2. **Start services**
```bash
docker compose up -d
```

3. **Run tests**
```bash
# Run all tests
pytest

# Run with parallel execution
pytest -n auto

# Run specific test categories
pytest -m crud
pytest -m auth
pytest -m validation
```

## Configuration

### Environment Variables

- `MONGODB_URL`: MongoDB connection string
- `MONGODB_DB_NAME`: Database name
- `JWT_SECRET_KEY`: JWT signing secret
- `API_BASE_URL`: FastAPI service URL (for tests)

### Test Configuration

Test settings are configured in `pytest.ini`:
- Parallel execution support
- Test markers for organization
- Coverage reporting
- Custom test discovery patterns

## Development

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_orders_crud_create.py

# Tests with specific markers
pytest -m "crud and create"

# Parallel execution
pytest -n 4

# With coverage
pytest --cov=app
```

### Test Markers

- `@pytest.mark.crud`: CRUD operation tests
- `@pytest.mark.auth`: Authentication tests
- `@pytest.mark.validation`: Input validation tests
- `@pytest.mark.slow`: Long-running tests

## System Assumptions

1. **Order Creation Status**: Regular users can only create orders with "Pending" status, while admins can create orders with any valid status
2. **Status Management**: Only admins can update order status to any valid state (Pending, Processing, Shipped, Delivered, Cancelled)
3. **Order Modifications**: Users have read-only access to their orders; only admins can update or delete orders
4. **Cancellation Support**: Orders support a "Cancelled" status for business workflow completeness

## Current Limitations

1. **Security Configuration**: MongoDB credentials (root/root_password) are exposed in configuration files for development purposes. Production deployments require proper secrets management
2. **Test Isolation**: Unit tests currently perform end-to-end API calls rather than isolated component testing. Delete tests, for example, create orders via API before deletion - Instead of inserting an order directly to the database and only deleting via an API request.
3. **Deployment Pipeline**: GitHub Actions workflow simulates deployment using a shell script rather than actual production deployment
4. **External Service Mocking**: Payment services, email notifications, and other external dependencies lack proper mocking and error scenario testing

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.