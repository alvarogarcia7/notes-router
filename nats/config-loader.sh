#!/bin/bash

# YAML configuration loader for bash applications
# Provides functions to read configuration from config.yaml

# Helper function to extract YAML value by key
# Handles quoted and unquoted values
extract_yaml_value() {
    local file="$1"
    local key="$2"
    local default="$3"

    if [ ! -f "$file" ]; then
        echo "$default"
        return
    fi

    # Look for the key in the file and extract value
    # Handles: key: "value" and key: value formats
    local value=$(grep "^[[:space:]]*$key:" "$file" | head -1 | sed 's/^[^:]*:[[:space:]]*//;s/^["'"'"']//;s/["'"'"']$//' | xargs)

    if [ -z "$value" ]; then
        echo "$default"
    else
        echo "$value"
    fi
}

# Get schema registry location from config.yaml
get_schema_registry() {
    local config_file="${1:-config.yaml}"
    extract_yaml_value "$config_file" "registry" "file://./schemas"
}

# Get NATS server from config.yaml
get_nats_server() {
    local config_file="${1:-config.yaml}"
    extract_yaml_value "$config_file" "nats_server" "localhost:4222"
}

# Get message directory from config.yaml
get_message_dir() {
    local config_file="${1:-config.yaml}"
    extract_yaml_value "$config_file" "message_dir" "/tmp/nats-poc-messages"
}
