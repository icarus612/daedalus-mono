package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"

	"github.com/dae-go/crud-server/pkg/client"
)

func main() {
	var (
		serverURL = flag.String("server", "http://localhost:8080", "Server URL")
		table     = flag.String("table", "", "Table name")
		create    = flag.String("create", "", "Create a record with key:value pairs (e.g., name:John,age:30)")
		list      = flag.Bool("list", false, "List all records in the table")
		update    = flag.String("update", "", "Update a record by ID with key:value pairs (e.g., 1,name:Jane,age:25)")
		deleteID  = flag.Int("delete", -1, "Delete a record by ID")
		json      = flag.Bool("json", false, "Output in JSON format")
	)

	flag.Parse()

	if *table == "" {
		log.Fatal("Table name is required")
	}

	c := client.NewClient(*serverURL)

	switch {
	case *create != "":
		createRecord(c, *table, *create)
	case *list:
		listRecords(c, *table, *json)
	case *update != "":
		updateRecord(c, *table, *update)
	case *deleteID >= 0:
		deleteRecord(c, *table, *deleteID)
	default:
		flag.Usage()
		os.Exit(1)
	}
}

func parseKeyValuePairs(input string) (map[string]interface{}, error) {
	record := make(map[string]interface{})
	pairs := strings.Split(input, ",")

	for _, pair := range pairs {
		parts := strings.Split(pair, ":")
		if len(parts) != 2 {
			return nil, fmt.Errorf("invalid format: %s (expected key:value)", pair)
		}

		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])

		// Try to parse as number
		if num, err := strconv.ParseFloat(value, 64); err == nil {
			record[key] = num
		} else if value == "true" || value == "false" {
			record[key] = value == "true"
		} else {
			record[key] = value
		}
	}

	return record, nil
}

func createRecord(c *client.Client, table, data string) {
	record, err := parseKeyValuePairs(data)
	if err != nil {
		log.Fatal(err)
	}

	if err := c.CreateRecord(table, record); err != nil {
		log.Fatal(err)
	}

	fmt.Println("Record created successfully")
}

func listRecords(c *client.Client, table string, jsonOutput bool) {
	records, err := c.GetRecords(table)
	if err != nil {
		log.Fatal(err)
	}

	if len(records) == 0 {
		fmt.Println("No records found")
		return
	}

	if jsonOutput {
		output, err := json.MarshalIndent(records, "", "  ")
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println(string(output))
	} else {
		fmt.Printf("Records in table '%s':\n", table)
		for _, record := range records {
			fmt.Printf("ID: %v\n", record["id"])
			for k, v := range record {
				if k != "id" {
					fmt.Printf("  %s: %v\n", k, v)
				}
			}
			fmt.Println()
		}
	}
}

func updateRecord(c *client.Client, table, data string) {
	parts := strings.SplitN(data, ",", 2)
	if len(parts) < 2 {
		log.Fatal("Invalid update format (expected: ID,key:value,key:value)")
	}

	id, err := strconv.Atoi(parts[0])
	if err != nil {
		log.Fatal("Invalid ID: ", parts[0])
	}

	record, err := parseKeyValuePairs(parts[1])
	if err != nil {
		log.Fatal(err)
	}

	record["id"] = id

	if err := c.UpdateRecord(table, record); err != nil {
		log.Fatal(err)
	}

	fmt.Printf("Record with ID %d updated successfully\n", id)
}

func deleteRecord(c *client.Client, table string, id int) {
	if err := c.DeleteRecord(table, id); err != nil {
		log.Fatal(err)
	}

	fmt.Printf("Record with ID %d deleted successfully\n", id)
}