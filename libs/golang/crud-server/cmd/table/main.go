package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/dae-go/crud-server/db"
	"github.com/dae-go/crud-server/pkg/client"
)

func main() {
	var (
		serverURL = flag.String("server", "http://localhost:8080", "Server URL")
		create    = flag.String("create", "", "Create a table with the given name")
		columns   = flag.String("columns", "", "Comma-separated list of column:type pairs (e.g., name:string,age:number)")
		list      = flag.Bool("list", false, "List all tables")
		delete    = flag.String("delete", "", "Delete a table with the given name")
	)

	flag.Parse()

	c := client.NewClient(*serverURL)

	switch {
	case *create != "":
		if *columns == "" {
			log.Fatal("Columns are required when creating a table")
		}
		createTable(c, *create, *columns)
	case *list:
		listTables(c)
	case *delete != "":
		deleteTable(c, *delete)
	default:
		flag.Usage()
		os.Exit(1)
	}
}

func createTable(c *client.Client, name, columnsStr string) {
	cols := strings.Split(columnsStr, ",")
	columns := make([]db.Column, 0, len(cols))

	for _, col := range cols {
		parts := strings.Split(col, ":")
		if len(parts) != 2 {
			log.Fatalf("Invalid column format: %s (expected name:type)", col)
		}
		columns = append(columns, db.Column{
			Name: strings.TrimSpace(parts[0]),
			Type: strings.TrimSpace(parts[1]),
		})
	}

	table := &db.Table{
		Name:    name,
		Columns: columns,
	}

	if err := c.CreateTable(table); err != nil {
		log.Fatal(err)
	}

	fmt.Printf("Table '%s' created successfully\n", name)
}

func listTables(c *client.Client) {
	tables, err := c.ListTables()
	if err != nil {
		log.Fatal(err)
	}

	if len(tables) == 0 {
		fmt.Println("No tables found")
		return
	}

	fmt.Println("Tables:")
	for _, table := range tables {
		fmt.Printf("  - %s\n", table)
	}
}

func deleteTable(c *client.Client, name string) {
	if err := c.DeleteTable(name); err != nil {
		log.Fatal(err)
	}

	fmt.Printf("Table '%s' deleted successfully\n", name)
}
