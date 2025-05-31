package main

import (
	"database/sql"
	"log"
	"net/http"

	pkg "github.com/dae-go/crud-server/pkg"
)

func main() {
	// Initialize database
	db, err := sql.Open("sqlite3", "./crud.db")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	server := &pkg.Server{db: db}

	// Routes
	http.HandleFunc("/tables", server.handleTables)
	http.HandleFunc("/tables/", server.handleTable)
	http.HandleFunc("/rows/", server.handleRows)

	log.Println("Server starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
