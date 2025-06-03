package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"

	"github.com/dae-go/crud-server/db"
	"github.com/dae-go/crud-server/pkg/client"
)

type Migration struct {
	Tables []db.Table `json:"tables"`
}

func main() {
	var (
		serverURL = flag.String("server", "http://localhost:8080", "Server URL")
		file      = flag.String("file", "", "Migration file (JSON)")
		export    = flag.String("export", "", "Export current schema to file")
	)

	flag.Parse()

	c := client.NewClient(*serverURL)

	switch {
	case *file != "":
		migrate(c, *file)
	case *export != "":
		exportSchema(c, *export)
	default:
		flag.Usage()
		os.Exit(1)
	}
}

func migrate(c *client.Client, filename string) {
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		log.Fatal("Failed to read migration file: ", err)
	}

	var migration Migration
	if err := json.Unmarshal(data, &migration); err != nil {
		log.Fatal("Failed to parse migration file: ", err)
	}

	// First, get existing tables
	existingTables, err := c.ListTables()
	if err != nil {
		log.Fatal("Failed to list existing tables: ", err)
	}

	// Delete existing tables
	for _, tableName := range existingTables {
		fmt.Printf("Dropping table '%s'...\n", tableName)
		if err := c.DeleteTable(tableName); err != nil {
			log.Printf("Warning: Failed to delete table '%s': %v\n", tableName, err)
		}
	}

	// Create new tables
	for _, table := range migration.Tables {
		fmt.Printf("Creating table '%s'...\n", table.Name)
		if err := c.CreateTable(&table); err != nil {
			log.Fatal("Failed to create table: ", err)
		}
	}

	fmt.Println("Migration completed successfully")
}

func exportSchema(c *client.Client, filename string) {
	tables, err := c.ListTables()
	if err != nil {
		log.Fatal("Failed to list tables: ", err)
	}

	// For now, we can only export table names since the API doesn't return column info
	// In a real implementation, we'd need an endpoint to get table schema
	migration := Migration{
		Tables: []db.Table{},
	}

	for _, tableName := range tables {
		migration.Tables = append(migration.Tables, db.Table{
			Name:    tableName,
			Columns: []db.Column{}, // Would need API endpoint to get columns
		})
	}

	data, err := json.MarshalIndent(migration, "", "  ")
	if err != nil {
		log.Fatal("Failed to marshal schema: ", err)
	}

	if err := ioutil.WriteFile(filename, data, 0644); err != nil {
		log.Fatal("Failed to write schema file: ", err)
	}

	fmt.Printf("Schema exported to %s\n", filename)
	fmt.Println("Note: Column information is not available through the current API")
}