#!/bin/bash

# 1. Create a conversation
echo "Creating conversation..."
CONV_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Thresholds"}')

# Extract conversation ID
CONV_ID=$(echo $CONV_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

echo "Created conversation: $CONV_ID"
echo "----------------------------------------"

# 2. Send the chat message
echo "Sending message to AI..."
curl -s -X POST "http://127.0.0.1:8000/api/v1/chat/$CONV_ID/send" \
  -H "Content-Type: application/json" \
  -d '{"message": "გამარჯობა, მაინტერესებს კანაფის ფისის (ჰაშიშის) ნარკოტიკული ზღვრები გრამებში. რაარის დიდი და მცირე ოდენობა?"}'

