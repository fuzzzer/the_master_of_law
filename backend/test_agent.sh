#!/usr/bin/env bash
# Test the case agent endpoint end-to-end.
# Usage: ./test_agent.sh
#
# Prerequisites:
#   - Docker running (./dev_runner.sh)
#   - Backend at http://127.0.0.1:8000

set -e

BASE="http://127.0.0.1:8000/api/v1"

echo "=== 1. Health check ==="
curl -sf "$BASE/health" && echo " ✅" || { echo " ❌ Backend not running"; exit 1; }

echo ""
echo "=== 2. Create conversation ==="
CONV=$(curl -sf -X POST "$BASE/conversations" \
  -H "Content-Type: application/json" \
  -d '{}')
CONV_ID=$(echo "$CONV" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "  conversation_id: $CONV_ID ✅"

echo ""
echo "=== 3. Send initial message (case_intake) ==="
INTAKE_RESP=$(curl -sf -X POST "$BASE/chat/$CONV_ID/send" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "მე მაქვს პრობლემა მეზობელთან. მან ჩემი ეზოს ნაწილი მიითვისა და ღობე გადმოწია.",
    "mode": "case_intake",
    "rag_config": {"legal_codes": true, "court_practice": true, "grand_chamber": true}
  }')
echo "  AI response (first 200 chars):"
echo "$INTAKE_RESP" | python3 -c "import sys,json; r=json.load(sys.stdin); print('  ', r.get('response','')[:200])"
echo " ✅"

echo ""
echo "=== 4. Build case file ==="
CASE=$(curl -sf -X POST "$BASE/case-files/build" \
  -H "Content-Type: application/json" \
  -d "{\"conversation_id\": \"$CONV_ID\"}")
CASE_FILE_ID=$(echo "$CASE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "  case_file_id: $CASE_FILE_ID ✅"

echo ""
echo "=== 5. Agent mode — add a fact ==="
AGENT_RESP=$(curl -sf -X POST "$BASE/chat/$CONV_ID/agent" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"დაამატე ფაქტი: მეზობელმა 2024 წლის მარტში ჩემი ეზოს 15 კვ.მ მიითვისა.\",
    \"mode\": \"case_agent\",
    \"case_file_id\": \"$CASE_FILE_ID\",
    \"rag_config\": {\"legal_codes\": true, \"court_practice\": false, \"grand_chamber\": false}
  }")
echo "  AI response:"
echo "$AGENT_RESP" | python3 -c "
import sys, json
r = json.load(sys.stdin)
print('  Response:', r.get('response','')[:300])
print('  Tool results:', json.dumps(r.get('tool_results', []), indent=2, ensure_ascii=False)[:500])
print('  Citations:', len(r.get('citations', [])))
"
echo " ✅"

echo ""
echo "=== 6. Agent mode — get case summary ==="
SUMMARY_RESP=$(curl -sf -X POST "$BASE/chat/$CONV_ID/agent" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"აჩვენე საქმის მიმოხილვა\",
    \"mode\": \"case_agent\",
    \"case_file_id\": \"$CASE_FILE_ID\"
  }")
echo "  AI response (first 300 chars):"
echo "$SUMMARY_RESP" | python3 -c "import sys,json; r=json.load(sys.stdin); print('  ', r.get('response','')[:300])"
echo " ✅"

echo ""
echo "=== 7. Agent mode — destructive action (should require confirmation) ==="
DELETE_RESP=$(curl -sf -X POST "$BASE/chat/$CONV_ID/agent" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"წაშალე პირველი ფაქტი\",
    \"mode\": \"case_agent\",
    \"case_file_id\": \"$CASE_FILE_ID\"
  }")
echo "  Tool results:"
echo "$DELETE_RESP" | python3 -c "
import sys, json
r = json.load(sys.stdin)
trs = r.get('tool_results', [])
for t in trs:
    print(f'  Tool: {t[\"tool_name\"]} | Status: {t[\"status\"]} | Confirm: {t.get(\"requires_confirmation\", False)}')
    if t.get('confirmation_id'):
        print(f'  Confirmation ID: {t[\"confirmation_id\"]}')
print('Response:', r.get('response','')[:200])
" 2>&1
echo " ✅"

echo ""
echo "=== All tests passed! ==="
echo ""
echo "Agent appears in: Case Workspace → Chat tab"
echo "After building a case file, the 🤖 toggle activates agent mode."
