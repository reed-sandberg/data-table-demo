#!/bin/bash
# Demo script for Data Tables API
# Run the server first: make run

set -e

BASE_URL="http://localhost:5000"

echo "=========================================="
echo "Data Tables API Demo"
echo "=========================================="
echo ""

# Health check
echo "1. Health Check"
echo "---------------"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

# Create a table
echo "2. Create Table 'customers'"
echo "---------------------------"
TABLE_RESPONSE=$(curl -s -X POST "$BASE_URL/tables" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "customers",
    "columns": [
      {"name": "name", "type": "string"},
      {"name": "age", "type": "number"},
      {"name": "active", "type": "boolean"}
    ]
  }')
echo "$TABLE_RESPONSE" | python3 -m json.tool
TABLE_ID=$(echo "$TABLE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Table ID: $TABLE_ID"
echo ""

# Get table details
echo "3. Get Table Details"
echo "--------------------"
curl -s "$BASE_URL/tables/$TABLE_ID" | python3 -m json.tool
echo ""

# Insert rows
echo "4. Insert Rows"
echo "--------------"
echo "Inserting Alice..."
ROW1_RESPONSE=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/rows" \
  -H "Content-Type: application/json" \
  -d '{"data": {"name": "Alice", "age": 30, "active": true}}')
echo "$ROW1_RESPONSE" | python3 -m json.tool
ROW1_ID=$(echo "$ROW1_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "Inserting Bob..."
curl -s -X POST "$BASE_URL/tables/$TABLE_ID/rows" \
  -H "Content-Type: application/json" \
  -d '{"data": {"name": "Bob", "age": 25, "active": true}}' | python3 -m json.tool

echo "Inserting Charlie..."
curl -s -X POST "$BASE_URL/tables/$TABLE_ID/rows" \
  -H "Content-Type: application/json" \
  -d '{"data": {"name": "Charlie", "age": 35, "active": false}}' | python3 -m json.tool
echo ""

# List all rows
echo "5. List All Rows"
echo "----------------"
curl -s "$BASE_URL/tables/$TABLE_ID/rows" | python3 -m json.tool
echo ""

# Filter rows
echo "6. Filter Rows (active=true)"
echo "----------------------------"
curl -s "$BASE_URL/tables/$TABLE_ID/rows?filter\[active\]=true" | python3 -m json.tool
echo ""

echo "7. Filter Rows (name=Alice)"
echo "---------------------------"
curl -s "$BASE_URL/tables/$TABLE_ID/rows?filter\[name\]=Alice" | python3 -m json.tool
echo ""

# Update schema - add column
echo "8. Add 'email' Column"
echo "---------------------"
curl -s -X PATCH "$BASE_URL/tables/$TABLE_ID/schema" \
  -H "Content-Type: application/json" \
  -d '{"add_columns": [{"name": "email", "type": "string"}]}' | python3 -m json.tool
echo ""

# Update row with new email field
echo "9. Update Alice with Email"
echo "--------------------------"
curl -s -X PUT "$BASE_URL/tables/$TABLE_ID/rows/$ROW1_ID" \
  -H "Content-Type: application/json" \
  -d '{"data": {"email": "alice@example.com"}}' | python3 -m json.tool
echo ""

# Pagination example
echo "10. Pagination (limit=2, offset=1)"
echo "-----------------------------------"
curl -s "$BASE_URL/tables/$TABLE_ID/rows?limit=2&offset=1" | python3 -m json.tool
echo ""

# Remove a column
echo "11. Remove 'age' Column"
echo "-----------------------"
curl -s -X PATCH "$BASE_URL/tables/$TABLE_ID/schema" \
  -H "Content-Type: application/json" \
  -d '{"remove_columns": ["age"]}' | python3 -m json.tool
echo ""

# Verify rows updated
echo "12. Verify Rows (age column removed)"
echo "------------------------------------"
curl -s "$BASE_URL/tables/$TABLE_ID/rows" | python3 -m json.tool
echo ""

# List tables
echo "13. List All Tables"
echo "-------------------"
curl -s "$BASE_URL/tables" | python3 -m json.tool
echo ""

# Delete row
echo "14. Delete a Row"
echo "----------------"
curl -s -X DELETE "$BASE_URL/tables/$TABLE_ID/rows/$ROW1_ID" -w "HTTP Status: %{http_code}\n"
echo ""

# Delete table
echo "15. Delete Table"
echo "----------------"
curl -s -X DELETE "$BASE_URL/tables/$TABLE_ID" -w "HTTP Status: %{http_code}\n"
echo ""

echo "=========================================="
echo "Demo Complete!"
echo "=========================================="

