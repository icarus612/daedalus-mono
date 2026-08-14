# Simple CRUD Server

A lightweight CRUD server built with Go's standard library that provides RESTful endpoints for managing tables and their data.

## Features

- Create, Read, Update, and Delete operations for tables and records
- In-memory storage with thread-safe operations
- JSON-based API
- No external dependencies - uses only Go standard library

## Project Structure

```
.
├── cmd/
│   ├── server/      # CRUD server
│   ├── table/       # Table management CLI
│   ├── row/         # Row/record management CLI
│   ├── migrate/     # Database migration CLI
│   └── seed/        # Database seeding CLI
├── db/
│   └── db.go        # Database package with storage logic
├── internal/
│   └── handlers.go  # HTTP handlers for API endpoints
├── pkg/
│   └── client/      # HTTP client for CLI tools
└── README.md        # This file
```

## API Endpoints

### Table Management

- **GET /table** - List all tables
  ```bash
  curl http://localhost:8080/table
  ```

- **POST /table** - Create a new table
  ```bash
  curl -X POST http://localhost:8080/table \
    -H "Content-Type: application/json" \
    -d '{"name": "users", "columns": [{"name": "name", "type": "string"}, {"name": "email", "type": "string"}]}'
  ```

- **DELETE /table** - Delete a table
  ```bash
  curl -X DELETE http://localhost:8080/table \
    -H "Content-Type: application/json" \
    -d '{"name": "users"}'
  ```

### Data Management

- **GET /tables/{tablename}** - Get all records from a table
  ```bash
  curl http://localhost:8080/tables/users
  ```

- **POST /tables/{tablename}** - Create a new record (id is auto-generated)
  ```bash
  curl -X POST http://localhost:8080/tables/users \
    -H "Content-Type: application/json" \
    -d '{"name": "John Doe", "email": "john@example.com"}'
  ```

- **PUT /tables/{tablename}** - Update a record (requires 'id' field)
  ```bash
  curl -X PUT http://localhost:8080/tables/users \
    -H "Content-Type: application/json" \
    -d '{"id": 1, "name": "John Updated", "email": "john.updated@example.com"}'
  ```

- **DELETE /tables/{tablename}** - Delete a record
  ```bash
  curl -X DELETE http://localhost:8080/tables/users \
    -H "Content-Type: application/json" \
    -d '{"id": 1}'
  ```

## Running the Server

```bash
go run cmd/server/main.go
```

The server will start on port 8080 by default.

## CLI Tools

The project includes several CLI tools for managing the database:

### Table Management

```bash
# List all tables
go run cmd/table/main.go -list

# Create a new table
go run cmd/table/main.go -create products -columns "name:string,price:number,stock:number"

# Delete a table
go run cmd/table/main.go -delete products
```

### Row Management

```bash
# List all records in a table
go run cmd/row/main.go -table products -list

# List records in JSON format
go run cmd/row/main.go -table products -list -json

# Create a new record
go run cmd/row/main.go -table products -create "name:Laptop,price:999.99,stock:15"

# Update a record (ID,field:value,field:value)
go run cmd/row/main.go -table products -update "1,name:Gaming Laptop,price:1299.99"

# Delete a record
go run cmd/row/main.go -table products -delete 1
```

### Database Migration

```bash
# Apply a migration from file
go run cmd/migrate/main.go -file schema.json

# Export current schema (limited functionality)
go run cmd/migrate/main.go -export current-schema.json
```

Example migration file (schema.json):
```json
{
  "tables": [
    {
      "name": "users",
      "columns": [
        {"name": "name", "type": "string"},
        {"name": "email", "type": "string"},
        {"name": "age", "type": "number"}
      ]
    },
    {
      "name": "products",
      "columns": [
        {"name": "name", "type": "string"},
        {"name": "price", "type": "number"},
        {"name": "stock", "type": "number"}
      ]
    }
  ]
}
```

### Database Seeding

```bash
# Seed database from file
go run cmd/seed/main.go -file seed-data.json

# Clear existing data before seeding
go run cmd/seed/main.go -file seed-data.json -clear
```

Example seed file (seed-data.json):
```json
{
  "seeds": [
    {
      "table": "users",
      "records": [
        {"name": "John Doe", "email": "john@example.com", "age": 30},
        {"name": "Jane Smith", "email": "jane@example.com", "age": 25}
      ]
    },
    {
      "table": "products",
      "records": [
        {"name": "Laptop", "price": 999.99, "stock": 10},
        {"name": "Mouse", "price": 29.99, "stock": 100}
      ]
    }
  ]
}
```

## Example Workflow

1. Start the server:
```bash
go run cmd/server/main.go
```

2. Create tables using migration:
```bash
go run cmd/migrate/main.go -file schema.json
```

3. Seed initial data:
```bash
go run cmd/seed/main.go -file seed-data.json
```

4. Work with data:
```bash
# List all users
go run cmd/row/main.go -table users -list

# Add a new user
go run cmd/row/main.go -table users -create "name:Bob Wilson,email:bob@example.com,age:35"

# Update a user
go run cmd/row/main.go -table users -update "3,email:bob.wilson@example.com"

# Delete a user
go run cmd/row/main.go -table users -delete 3
```

## Data Model

### Table
```json
{
  "name": "table_name",
  "columns": [
    {"name": "column1", "type": "string"},
    {"name": "column2", "type": "number"}
  ]
}
```

### Record
Records are flexible JSON objects. The id field is auto-generated when creating new records (as an incrementing integer). For UPDATE and DELETE operations, the id field is required.

## Additional Endpoints

- **GET /** - API information
- **GET /health** - Health check endpoint

## Notes

- All data is stored in memory and will be lost when the server stops
- Thread-safe operations using mutex locks
- No schema validation beyond table column definitions
- IDs are auto-generated as incrementing integers when creating records
- The server includes request logging middleware
- Graceful shutdown is supported (Ctrl+C)