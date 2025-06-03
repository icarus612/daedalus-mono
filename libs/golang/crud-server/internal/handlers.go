package internal

import (
	"github.com/dae-go/crud-server/db"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
)

// Server represents our HTTP server
type Server struct {
	DB *db.Database
}

// NewServer creates a new server instance
func NewServer() *Server {
	return &Server{
		DB: db.NewDatabase(),
	}
}

// HandleTable handles table CRUD operations
func (s *Server) HandleTable(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	switch r.Method {
	case http.MethodGet:
		s.listTables(w, r)
	case http.MethodPost:
		s.createTable(w, r)
	case http.MethodDelete:
		s.deleteTable(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// HandleTableData handles data CRUD operations
func (s *Server) HandleTableData(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// Extract table name from path
	path := strings.TrimPrefix(r.URL.Path, "/tables/")
	if path == "" || strings.Contains(path, "/") {
		http.Error(w, "Invalid table name", http.StatusBadRequest)
		return
	}
	tableName := path

	switch r.Method {
	case http.MethodGet:
		s.getRecords(w, r, tableName)
	case http.MethodPost:
		s.createRecord(w, r, tableName)
	case http.MethodPut:
		s.updateRecord(w, r, tableName)
	case http.MethodDelete:
		s.deleteRecord(w, r, tableName)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// Table operations

func (s *Server) listTables(w http.ResponseWriter, r *http.Request) {
	tables := s.DB.ListTables()
	if err := json.NewEncoder(w).Encode(tables); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (s *Server) createTable(w http.ResponseWriter, r *http.Request) {
	var table db.Table
	if err := json.NewDecoder(r.Body).Decode(&table); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if table.Name == "" || len(table.Columns) == 0 {
		http.Error(w, "Table name and columns are required", http.StatusBadRequest)
		return
	}

	if err := s.DB.CreateTable(&table); err != nil {
		http.Error(w, err.Error(), http.StatusConflict)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"message": "Table created successfully"})
}

func (s *Server) deleteTable(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name string `json:"name"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if req.Name == "" {
		http.Error(w, "Table name is required", http.StatusBadRequest)
		return
	}

	if err := s.DB.DeleteTable(req.Name); err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	json.NewEncoder(w).Encode(map[string]string{"message": "Table deleted successfully"})
}

// Data operations

func (s *Server) getRecords(w http.ResponseWriter, r *http.Request, tableName string) {
	records, err := s.DB.GetRecords(tableName)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	if err := json.NewEncoder(w).Encode(records); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (s *Server) createRecord(w http.ResponseWriter, r *http.Request, tableName string) {
	var record map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&record); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if err := s.DB.InsertRecord(tableName, record); err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"message": "Record created successfully"})
}

func (s *Server) updateRecord(w http.ResponseWriter, r *http.Request, tableName string) {
	var record map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&record); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if err := s.DB.UpdateRecord(tableName, record); err != nil {
		if err.Error() == "record must have an 'id' field" {
			http.Error(w, err.Error(), http.StatusBadRequest)
		} else {
			http.Error(w, err.Error(), http.StatusNotFound)
		}
		return
	}

	json.NewEncoder(w).Encode(map[string]string{"message": "Record updated successfully"})
}

func (s *Server) deleteRecord(w http.ResponseWriter, r *http.Request, tableName string) {
	var req struct {
		ID interface{} `json:"id"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if req.ID == nil {
		http.Error(w, "ID is required", http.StatusBadRequest)
		return
	}

	if err := s.DB.DeleteRecord(tableName, req.ID); err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	json.NewEncoder(w).Encode(map[string]string{"message": "Record deleted successfully"})
}

// SetupRoutes sets up all HTTP routes
func (s *Server) SetupRoutes() *http.ServeMux {
	mux := http.NewServeMux()

	// Table endpoints
	mux.HandleFunc("/table", s.HandleTable)

	// Table data endpoints - match any path starting with /tables/
	mux.HandleFunc("/tables/", s.HandleTableData)

	// Health check
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
	})

	// Root endpoint
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{
			"message":   "CRUD Server API",
			"version":   "1.0",
			"endpoints": "See README.md for API documentation",
		})
	})

	return mux
}

// LoggingMiddleware logs all HTTP requests
func LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Printf("[%s] %s %s\n", r.Method, r.URL.Path, r.RemoteAddr)
		next.ServeHTTP(w, r)
	})
}
