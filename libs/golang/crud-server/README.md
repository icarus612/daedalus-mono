# Simple CRUD Server

A lightweight CRUD server built with Go standard library only. Supports table management and data operations.

## Running the Server

```bash
go run main.go crud.go
```

The server will start on `http://localhost:8080`

## API Endpoints

### Table Management

#### List all tables
```bash
GET /tables
```

#### Create a new table
```bash
POST /tables
Content-Type: application/json

{
  "name": "users",
  "columns": {
    "name": "string",
    "email": "string",
    "age": "integer"
  }
}
```

#### Update table schema
```bash
PUT /tables
Content-Type: application/json

{
  "name": "users",
  "columns": {
    "name": "string",
    "email": "string",
    "age": "integer",
    "status": "string"
  }
}
```

#### Delete a table
```bash
DELETE /tables
Content-Type: application/json

{
  "name": "users"
}
```

### Data Management

#### List all records in a table
```bash
GET /tables/users/data
```

#### Get a specific record
```bash
GET /tables/users/data/1
```

#### Create a new record
```bash
POST /tables/users/data
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "age": 30
}
```

#### Update a record
```bash
PUT /tables/users/data/1
Content-Type: application/json

{
  "age": 31,
  "status": "active"
}
```

#### Delete a record
```bash
DELETE /tables/users/data/1
```

## Example Usage with curl

### 1. Create a table
```bash
curl -X POST http://localhost:8080/tables \
  -H "Content-Type: application/json" \
  -d '{
    "name": "products",
    "columns": {
      "name": "string",
      "price": "float",
      "category": "string"
    }
  }'
```

### 2. Add some data
```bash
curl -X POST http://localhost:8080/tables/products/data \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "price": 999.99,
    "category": "Electronics"
  }'

curl -X POST http://localhost:8080/tables/products/data \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Coffee Mug",
    "price": 15.50,
    "category": "Kitchen"
  }'
```

### 3. List all products
```bash
curl http://localhost:8080/tables/products/data
```

### 4. Update a product
```bash
curl -X PUT http://localhost:8080/tables/products/data/1 \
  -H "Content-Type: application/json" \
  -d '{
    "price": 899.99
  }'
```

### 5. Get a specific product
```bash
curl http://localhost:8080/tables/products/data/1
```

### 6. Delete a product
```bash
curl -X DELETE http://localhost:8080/tables/products/data/2
```

### 7. List all tables
```bash
curl http://localhost:8080/tables
```

## Features

- **Thread-safe**: Uses sync.RWMutex for concurrent access
- **In-memory storage**: Data is stored in memory (not persistent)
- **Auto-incrementing IDs**: Records get automatic integer IDs
- **JSON API**: All communication uses JSON format
- **Standard library only**: No external dependencies
- **Modular design**: Separated into main and package files

## Project Structure

- `main.go` - Server setup and routing
- `crud.go` - Core CRUD functionality and HTTP handlers
- `README.md` - Documentation and examples

## Response Formats

### Success Responses
- **200 OK**: Successful GET/PUT operations
- **201 Created**: Successful POST operations

### Error Responses
- **400 Bad Request**: Invalid JSON or missing required fields
- **404 Not Found**: Table or record not found
- **405 Method Not Allowed**: HTTP method not supported
- **409 Conflict**: Table already exists

All responses include appropriate JSON content with error messages for failures.