package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"

	"github.com/dae-go/crud-server/pkg/client"
)

type SeedData struct {
	Table   string                   `json:"table"`
	Records []map[string]interface{} `json:"records"`
}

type SeedFile struct {
	Seeds []SeedData `json:"seeds"`
}

func main() {
	var (
		serverURL = flag.String("server", "http://localhost:8080", "Server URL")
		file      = flag.String("file", "", "Seed data file (JSON)")
		clear     = flag.Bool("clear", false, "Clear existing data before seeding")
	)

	flag.Parse()

	if *file == "" {
		flag.Usage()
		os.Exit(1)
	}

	c := client.NewClient(*serverURL)

	seedDatabase(c, *file, *clear)
}

func seedDatabase(c *client.Client, filename string, clearData bool) {
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		log.Fatal("Failed to read seed file: ", err)
	}

	var seedFile SeedFile
	if err := json.Unmarshal(data, &seedFile); err != nil {
		log.Fatal("Failed to parse seed file: ", err)
	}

	for _, seed := range seedFile.Seeds {
		fmt.Printf("Seeding table '%s'...\n", seed.Table)

		if clearData {
			// Get existing records and delete them
			records, err := c.GetRecords(seed.Table)
			if err != nil {
				log.Printf("Warning: Failed to get records from '%s': %v\n", seed.Table, err)
			} else {
				for _, record := range records {
					if id, ok := record["id"]; ok {
						if err := c.DeleteRecord(seed.Table, id); err != nil {
							log.Printf("Warning: Failed to delete record %v: %v\n", id, err)
						}
					}
				}
			}
		}

		// Insert new records
		for i, record := range seed.Records {
			if err := c.CreateRecord(seed.Table, record); err != nil {
				log.Printf("Failed to insert record %d in table '%s': %v\n", i+1, seed.Table, err)
			}
		}

		fmt.Printf("  Inserted %d records\n", len(seed.Records))
	}

	fmt.Println("Seeding completed successfully")
}

// Example seed file format:
/*
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
*/