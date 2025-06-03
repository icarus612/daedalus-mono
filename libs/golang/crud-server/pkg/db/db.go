package db

import (
	"errors"
	"fmt"
	"sync"
)

type Column struct {
	Name string `json:"name"`
	Type string `json:"type"`
}

type Table struct {
	Name    string   `json:"name"`
	Columns []Column `json:"columns"`
}

type Database struct {
	mu     sync.RWMutex
	tables map[string]*tableData
}

type tableData struct {
	table   *Table
	records []map[string]any
	nextID  int
}

func NewDatabase() *Database {
	return &Database{
		tables: make(map[string]*tableData),
	}
}

func (db *Database) CreateTable(table *Table) error {
	db.mu.Lock()
	defer db.mu.Unlock()

	if _, exists := db.tables[table.Name]; exists {
		return fmt.Errorf("table %s already exists", table.Name)
	}

	db.tables[table.Name] = &tableData{
		table:   table,
		records: []map[string]any{},
		nextID:  1,
	}

	return nil
}

func (db *Database) ListTables() []string {
	db.mu.RLock()
	defer db.mu.RUnlock()

	tables := make([]string, 0, len(db.tables))
	for name := range db.tables {
		tables = append(tables, name)
	}
	return tables
}

func (db *Database) DeleteTable(name string) error {
	db.mu.Lock()
	defer db.mu.Unlock()

	if _, exists := db.tables[name]; !exists {
		return fmt.Errorf("table %s not found", name)
	}

	delete(db.tables, name)
	return nil
}

func (db *Database) GetRecords(tableName string) ([]map[string]any, error) {
	db.mu.RLock()
	defer db.mu.RUnlock()

	tableData, exists := db.tables[tableName]
	if !exists {
		return nil, fmt.Errorf("table %s not found", tableName)
	}

	result := make([]map[string]any, len(tableData.records))
	copy(result, tableData.records)
	return result, nil
}

func (db *Database) InsertRecord(tableName string, record map[string]any) error {
	db.mu.Lock()
	defer db.mu.Unlock()

	tableData, exists := db.tables[tableName]
	if !exists {
		return fmt.Errorf("table %s not found", tableName)
	}

	newRecord := make(map[string]any)
	for k, v := range record {
		newRecord[k] = v
	}

	newRecord["id"] = tableData.nextID
	tableData.nextID++

	tableData.records = append(tableData.records, newRecord)
	return nil
}

func (db *Database) UpdateRecord(tableName string, record map[string]any) error {
	db.mu.Lock()
	defer db.mu.Unlock()

	tableData, exists := db.tables[tableName]
	if !exists {
		return fmt.Errorf("table %s not found", tableName)
	}

	id, hasID := record["id"]
	if !hasID {
		return errors.New("record must have an 'id' field")
	}

	for i, r := range tableData.records {
		if r["id"] == id {
			for k, v := range record {
				tableData.records[i][k] = v
			}
			return nil
		}
	}

	return fmt.Errorf("record with id %v not found", id)
}

func (db *Database) DeleteRecord(tableName string, id any) error {
	db.mu.Lock()
	defer db.mu.Unlock()

	tableData, exists := db.tables[tableName]
	if !exists {
		return fmt.Errorf("table %s not found", tableName)
	}

	for i, r := range tableData.records {
		if r["id"] == id {
			tableData.records = append(tableData.records[:i], tableData.records[i+1:]...)
			return nil
		}
	}

	return fmt.Errorf("record with id %v not found", id)
}
