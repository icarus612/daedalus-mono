package crud

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"maps"
)

type Item struct {
	ID    string  `json:"id"`
	Name  string  `json:"name"`
	Price float64 `json:"price"`
}

type RouteMap map[string]func(http.ResponseWriter, *http.Request)
type LogMap map[string]*log.Logger
type BasicCRUD struct {
	Routes RouteMap
	Port   string
	Items  []Item
	Logs   LogMap
}

func NewBasicCRUD(p ...string) BasicCRUD {
	var (
		port   = "8088"
		routes = RouteMap{}
	)
	if len(p) > 0 {
		port = p[0]
	}

	b := BasicCRUD{
		Routes: routes,
		Port:   port,
	}

	b.CreateLog()

	return b
}

func (b *BasicCRUD) updateLogOutput() {
	logsSlice := []io.Writer{os.Stdout}
	for _, v := range b.Logs {
		logsSlice = append(logsSlice, v.Writer())
	}
	log.SetOutput(io.MultiWriter(logsSlice...))
}

func (b *BasicCRUD) CreateLog(key string, logArgs ...string) {
	var (
		location   string
		prefix     string
		newLogFile os.File
	)

	if len(logArgs) > 0 {
		location = logArgs[0]
		newLogFile, err := os.Create(location)
		defer newLogFile.Close()
		if err != nil {
			fmt.Println("Error creating error.log file:", err)
			os.Exit(1)
		}
	}

	if len(logArgs) > 1 {

	}
	errLogger := log.New(newLogFile, prefix, log.Ldate|log.Ltime|log.Lshortfile)
	b.SetLog("error", errLogger)

}
func (b *BasicCRUD) SetLog(key string, val *log.Logger) {
	b.Logs[key] = val
	b.updateLogOutput()
}

func (b *BasicCRUD) UpdateLogs(l LogMap) {
	maps.Copy(b.Logs, l)
	b.updateLogOutput()
}

func (b BasicCRUD) Serve() {

	for route, handler := range b.Routes {
		http.HandleFunc(route, handler)
	}

	// Start the HTTP server on port 8080
	if err := http.ListenAndServe(":"+b.Port, nil); err != nil {
		b.Logs["error"].Fatalln(err)
	}
}

func (b *BasicCRUD) GetItems(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(b.Items)
}

func (b *BasicCRUD) HandleItem(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		b.GetItem(w, r)
	case r.Method:
		b.CreateItem(w, r)
	case http.MethodPut:
		b.UpdateItem(w, r)
	case http.MethodDelete:
		b.DeleteItem(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (b *BasicCRUD) GetItem(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	id := r.URL.Path[len("/items/"):]
	for _, item := range b.Items {
		if item.ID == id {
			json.NewEncoder(w).Encode(item)
			return
		}
	}
	http.NotFound(w, r)
}

func (b *BasicCRUD) CreateItem(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	var newItem Item
	json.NewDecoder(r.Body).Decode(&newItem)
	b.Items = append(b.Items, newItem)
	json.NewEncoder(w).Encode(newItem)
}

func (b *BasicCRUD) UpdateItem(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	id := r.URL.Path[len("/items/"):]
	for index, item := range b.Items {
		if item.ID == id {
			json.NewDecoder(r.Body).Decode(&b.Items[index])
			json.NewEncoder(w).Encode(b.Items[index])
			return
		}
	}
	http.NotFound(w, r)
}

func (b *BasicCRUD) DeleteItem(w http.ResponseWriter, r *http.Request) {
	id := r.URL.Path[len("/items/"):]
	for index, item := range b.Items {
		if item.ID == id {
			b.Items = append(b.Items[:index], b.Items[index+1:]...)
			w.WriteHeader(http.StatusNoContent)
			return
		}
	}
	http.NotFound(w, r)
}
