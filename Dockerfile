FROM python:3.10

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

# -----------------------------------------------------------------
# Copy certificates to make use of free open ai usage within the lab
# REMOVE THIS WHEN DEPLOYING TO CODE ENGINE

# Copy the certs directory (which may or may not contain certificates)
COPY certs /tmp/certs

# Copy any .crt files to the CA certificates directory and update trust store
RUN mkdir -p /usr/local/share/ca-certificates && \
    if [ -f /tmp/certs/rootCA.crt ]; then \
        cp /tmp/certs/rootCA.crt /usr/local/share/ca-certificates/rootCA.crt && \
        chmod 644 /usr/local/share/ca-certificates/rootCA.crt && \
        update-ca-certificates; \
    fi && \
    rm -rf /tmp/certs

# Set the environment variable OPENAI_API_KEY to empty string
ENV OPENAI_API_KEY=skills-network
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
# -----------------------------------------------------------------

CMD ["python", "-u", "server.py"]