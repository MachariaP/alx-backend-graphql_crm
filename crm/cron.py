"""
CRM Cron Jobs
Heartbeat logger for CRM application health monitoring.
"""

import os
import sys
from datetime import datetime
import logging
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Set up logging
log_file = "/tmp/crm_heartbeat_log.txt"

def log_crm_heartbeat():
    """
    Log a heartbeat message every 5 minutes to confirm CRM application health.
    Logs to /tmp/crm_heartbeat_log.txt in format: DD/MM/YYYY-HH:MM:SS CRM is alive
    Optionally queries GraphQL hello field to verify endpoint is responsive.
    """
    
    # Get current timestamp in required format
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{timestamp} CRM is alive"
    
    # Log to file (append mode)
    try:
        with open(log_file, 'a') as f:
            f.write(message + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")
    
    # Print to console for cron logging
    print(message)
    
    # Optional: Query GraphQL hello field to verify endpoint
    try:
        # Set up GraphQL client
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=True,
            retries=2,
            timeout=10
        )
        
        client = Client(
            transport=transport,
            fetch_schema_from_transport=True,
        )
        
        # Query the hello field (assuming it exists in your schema)
        query = gql("""
            query {
                hello
            }
        """)
        
        result = client.execute(query)
        
        if result and 'hello' in result:
            graphql_status = "GraphQL endpoint is responsive"
            print(graphql_status)
            
            # Also log to file
            with open(log_file, 'a') as f:
                f.write(f"{timestamp} {graphql_status}\n")
                
    except Exception as e:
        error_msg = f"GraphQL endpoint check failed: {str(e)}"
        print(error_msg)
        
        # Log error to file
        with open(log_file, 'a') as f:
            f.write(f"{timestamp} {error_msg}\n")
    
    return message
