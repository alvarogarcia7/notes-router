#!/usr/bin/env bash
set -e

CERTS_DIR="$(cd "$(dirname "$0")" && pwd)/certs"
mkdir -p "$CERTS_DIR"
cd "$CERTS_DIR"

echo "Generating TLS certificates for NATS..."

# Root CA
echo "  Generating root CA..."
openssl genpkey -algorithm ed25519 -out rootCA.key 2>/dev/null
openssl req -new -x509 -key rootCA.key -out rootCA.pem -days 3650 \
    -subj "/CN=NATS-Root-CA" 2>/dev/null

# Server cert (SAN covers how clients address the server)
echo "  Generating server certificate..."
openssl genpkey -algorithm ed25519 -out server.key 2>/dev/null
openssl req -new -key server.key -out server.csr -subj "/CN=nats-server" 2>/dev/null
openssl x509 -req -in server.csr \
    -CA rootCA.pem -CAkey rootCA.key -CAcreateserial \
    -out server.pem -days 365 \
    -extfile <(printf "subjectAltName=DNS:docker,DNS:localhost,IP:127.0.0.1") 2>/dev/null

# Client cert (CN becomes the mapped NATS user)
echo "  Generating client certificate..."
openssl genpkey -algorithm ed25519 -out client.key 2>/dev/null
openssl req -new -key client.key -out client.csr -subj "/CN=pipeline-client" 2>/dev/null
openssl x509 -req -in client.csr \
    -CA rootCA.pem -CAkey rootCA.key -CAcreateserial \
    -out client.pem -days 365 2>/dev/null

chmod 600 *.key
rm -f *.csr *.srl

echo "✓ Certificates generated in $CERTS_DIR"
