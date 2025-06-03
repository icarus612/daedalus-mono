package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"github.com/dae-go/crud-server/pkg/db"
)

type Client struct {
	baseURL string
	client  *http.Client
}

func NewClient(baseURL string) *Client {
	return &Client{
		baseURL: baseURL,
		client:  &http.Client{},
	}
}

func (c *Client) CreateTable(table *db.Table) error {
	data, err := json.Marshal(table)
	if err != nil {
		return err
	}

	resp, err := c.client.Post(c.baseURL+"/table", "application/json", bytes.NewBuffer(data))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("failed to create table: %s", string(body))
	}

	return nil
}

func (c *Client) ListTables() ([]string, error) {
	resp, err := c.client.Get(c.baseURL + "/table")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("failed to list tables: %s", string(body))
	}

	var tables []string
	if err := json.NewDecoder(resp.Body).Decode(&tables); err != nil {
		return nil, err
	}

	return tables, nil
}

func (c *Client) DeleteTable(name string) error {
	data, err := json.Marshal(map[string]string{"name": name})
	if err != nil {
		return err
	}

	req, err := http.NewRequest(http.MethodDelete, c.baseURL+"/table", bytes.NewBuffer(data))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("failed to delete table: %s", string(body))
	}

	return nil
}

func (c *Client) GetRecords(tableName string) ([]map[string]interface{}, error) {
	resp, err := c.client.Get(c.baseURL + "/tables/" + tableName)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("failed to get records: %s", string(body))
	}

	var records []map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&records); err != nil {
		return nil, err
	}

	return records, nil
}

func (c *Client) CreateRecord(tableName string, record map[string]interface{}) error {
	data, err := json.Marshal(record)
	if err != nil {
		return err
	}

	resp, err := c.client.Post(c.baseURL+"/tables/"+tableName, "application/json", bytes.NewBuffer(data))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("failed to create record: %s", string(body))
	}

	return nil
}

func (c *Client) UpdateRecord(tableName string, record map[string]interface{}) error {
	data, err := json.Marshal(record)
	if err != nil {
		return err
	}

	req, err := http.NewRequest(http.MethodPut, c.baseURL+"/tables/"+tableName, bytes.NewBuffer(data))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("failed to update record: %s", string(body))
	}

	return nil
}

func (c *Client) DeleteRecord(tableName string, id interface{}) error {
	data, err := json.Marshal(map[string]interface{}{"id": id})
	if err != nil {
		return err
	}

	req, err := http.NewRequest(http.MethodDelete, c.baseURL+"/tables/"+tableName, bytes.NewBuffer(data))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("failed to delete record: %s", string(body))
	}

	return nil
}
