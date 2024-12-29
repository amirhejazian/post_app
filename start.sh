#!/bin/bash

echo "Copying env file"
cp default.env .env
docker compose up -d