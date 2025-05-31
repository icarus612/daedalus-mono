package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"

	_ "github.com/mattn/go-sqlite3"
)

type Server struct {
	db *sql.DB
}

// Column represents a table column definition
type Column struct {
	Name     string `json:"name"`
	DataType string `json:"dataType"` // TEXT, INTEGER, REAL, BLOB
	NotNull  bool   `json:"notNull"`
	Primary  bool   `json:"primary"`
}

// TableSchema represents a table schema
type TableSchema struct {
	TableName string   `json:"tableName"`
	Columns   []Column `json:"columns"`
}

// Row represents generic row data
type Row map[string]interface{}

func main() {
	// Initialize database
	db, err := sql.Open("sqlite3", "./crud.db")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	server := &Server{db: db}

	// Routes
	http.HandleFunc("/tables", server.handleTables)
	http.HandleFunc("/tables/", server.handleTable)
	http.HandleFunc("/rows/", server.handleRows)

	log.Println("Server starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

// handleTables - GET all tables or POST to create new table
func (s *Server) handleTables(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case "GET":
		s.listTables(w, r)
	case "POST":
		s.createTable(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleTable - GET schema, DELETE table, or PUT to modify
func (s *Server) handleTable(w http.ResponseWriter, r *http.Request) {
	tableName := strings.TrimPrefix(r.URL.Path, "/tables/")

	switch r.Method {
	case "GET":
		s.getTableSchema(w, r, tableName)
	case "DELETE":
		s.deleteTable(w, r, tableName)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleRows - CRUD operations on rows
func (s *Server) handleRows(w http.ResponseWriter, r *http.Request) {
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/rows/"), "/")
	if len(parts) < 1 {
		http.Error(w, "Invalid path", http.StatusBadRequest)
		return
	}

	tableName := parts[0]

	switch r.Method {
	case "GET":
		if len(parts) > 1 {
			s.getRow(w, r, tableName, parts[1])
		} else {
			s.listRows(w, r, tableName)
		}
	case "POST":
		s.createRow(w, r, tableName)
	case "PUT":
		if len(parts) > 1 {
			s.updateRow(w, r, tableName, parts[1])
		} else {
			http.Error(w, "Row ID required", http.StatusBadRequest)
		}
	case "DELETE":
		if len(parts) > 1 {
			s.deleteRow(w, r, tableName, parts[1])
		} else {
			http.Error(w, "Row ID required", http.StatusBadRequest)
		}
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// Table operations

func (s *Server) listTables(w http.ResponseWriter, r *http.Request) {
	rows, err := s.db.Query(`
		SELECT name FROM sqlite_master 
		WHERE type='table' AND name NOT LIKE 'sqlite_%'
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var tables []string
	for rows.Next() {
		var name string
		if err := rows.Scan(&name); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		tables = append(tables, name)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(tables)
}

func (s *Server) createTable(w http.ResponseWriter, r *http.Request) {
	var schema TableSchema
	if err := json.NewDecoder(r.Body).Decode(&schema); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Build CREATE TABLE statement
	var columnDefs []string
	for _, col := range schema.Columns {
		def := fmt.Sprintf("%s %s", col.Name, col.DataType)
		if col.Primary {
			def += " PRIMARY KEY"
		}
		if col.NotNull && !col.Primary {
			def += " NOT NULL"
		}
		columnDefs = append(columnDefs, def)
	}

	query := fmt.Sprintf("CREATE TABLE %s (%s)", schema.TableName, strings.Join(columnDefs, ", "))

	if _, err := s.db.Exec(query); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"message": "Table created successfully"})
}

func (s *Server) getTableSchema(w http.ResponseWriter, r *http.Request, tableName string) {
	rows, err := s.db.Query(fmt.Sprintf("PRAGMA table_info(%s)", tableName))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var columns []Column
	for rows.Next() {
		var cid int
		var name, dataType string
		var notNull, pk int
		var dfltValue interface{}

		if err := rows.Scan(&cid, &name, &dataType, &notNull, &dfltValue, &pk); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		columns = append(columns, Column{
			Name:     name,
			DataType: dataType,
			NotNull:  notNull == 1,
			Primary:  pk == 1,
		})
	}

	if len(columns) == 0 {
		http.Error(w, "Table not found", http.StatusNotFound)
		return
	}

	schema := TableSchema{
		TableName: tableName,
		Columns:   columns,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(schema)
}

func (s *Server) deleteTable(w http.ResponseWriter, r *http.Request, tableName string) {
	query := fmt.Sprintf("DROP TABLE %s", tableName)

	if _, err := s.db.Exec(query); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Table deleted successfully"})
}

// Row operations

func (s *Server) listRows(w http.ResponseWriter, r *http.Request, tableName string) {
	// Get limit and offset from query params
	limit := r.URL.Query().Get("limit")
	offset := r.URL.Query().Get("offset")

	query := fmt.Sprintf("SELECT * FROM %s", tableName)
	if limit != "" {
		query += fmt.Sprintf(" LIMIT %s", limit)
		if offset != "" {
			query += fmt.Sprintf(" OFFSET %s", offset)
		}
	}

	rows, err := s.db.Query(query)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	// Get column names
	columns, err := rows.Columns()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	var results []Row
	for rows.Next() {
		values := make([]interface{}, len(columns))
		valuePtrs := make([]interface{}, len(columns))
		for i := range columns {
			valuePtrs[i] = &values[i]
		}

		if err := rows.Scan(valuePtrs...); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		row := make(Row)
		for i, col := range columns {
			row[col] = values[i]
		}
		results = append(results, row)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

func (s *Server) getRow(w http.ResponseWriter, r *http.Request, tableName, id string) {
	query := fmt.Sprintf("SELECT * FROM %s WHERE rowid = ?", tableName)

	row := s.db.QueryRow(query, id)

	// First, get column names
	colQuery := fmt.Sprintf("SELECT * FROM %s LIMIT 0", tableName)
	cols, err := s.db.Query(colQuery)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	columns, _ := cols.Columns()
	cols.Close()

	// Scan row
	values := make([]interface{}, len(columns))
	valuePtrs := make([]interface{}, len(columns))
	for i := range columns {
		valuePtrs[i] = &values[i]
	}

	if err := row.Scan(valuePtrs...); err != nil {
		if err == sql.ErrNoRows {
			http.Error(w, "Row not found", http.StatusNotFound)
		} else {
			http.Error(w, err.Error(), http.StatusInternalServerError)
		}
		return
	}

	result := make(Row)
	for i, col := range columns {
		result[col] = values[i]
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (s *Server) createRow(w http.ResponseWriter, r *http.Request, tableName string) {
	var row Row
	if err := json.NewDecoder(r.Body).Decode(&row); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Build INSERT statement
	var columns []string
	var placeholders []string
	var values []interface{}

	for col, val := range row {
		columns = append(columns, col)
		placeholders = append(placeholders, "?")
		values = append(values, val)
	}

	query := fmt.Sprintf("INSERT INTO %s (%s) VALUES (%s)",
		tableName,
		strings.Join(columns, ", "),
		strings.Join(placeholders, ", "))

	result, err := s.db.Exec(query, values...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	id, _ := result.LastInsertId()

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message": "Row created successfully",
		"id":      id,
	})
}

func (s *Server) updateRow(w http.ResponseWriter, r *http.Request, tableName, id string) {
	var row Row
	if err := json.NewDecoder(r.Body).Decode(&row); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Build UPDATE statement
	var setClauses []string
	var values []interface{}

	for col, val := range row {
		setClauses = append(setClauses, fmt.Sprintf("%s = ?", col))
		values = append(values, val)
	}
	values = append(values, id)

	query := fmt.Sprintf("UPDATE %s SET %s WHERE rowid = ?",
		tableName,
		strings.Join(setClauses, ", "))

	result, err := s.db.Exec(query, values...)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		http.Error(w, "Row not found", http.StatusNotFound)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Row updated successfully"})
}

func (s *Server) deleteRow(w http.ResponseWriter, _ *http.Request, tableName, id string) {
	query := fmt.Sprintf("DELETE FROM %s WHERE rowid = ?", tableName)

	result, err := s.db.Exec(query, id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		http.Error(w, "Row not found", http.StatusNotFound)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Row deleted successfully"})
}
