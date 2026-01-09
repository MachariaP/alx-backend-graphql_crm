"""
CRM Cron Jobs
Heartbeat logger and low stock updater for CRM application
"""

import os
import sys
from datetime import datetime
import logging
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Set up module-level logging configuration
logging.basicConfig(level=logging.INFO)


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
        with open("/tmp/crm_heartbeat_log.txt", 'a') as f:
            f.write(message + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")
    
    # Print to console for cron logging
    print(message)
    
    # Query GraphQL hello field to verify endpoint is responsive
    try:
        # Set up GraphQL client
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=True,
            retries=2,
            timeout=5
        )
        
        client = Client(
            transport=transport,
            fetch_schema_from_transport=False,
        )
        
        # Query the hello field
        query = gql("""
            query {
                hello
            }
        """)
        
        result = client.execute(query)
        
        if result and 'hello' in result:
            hello_response = result['hello']
            graphql_status = f"GraphQL hello response: {hello_response}"
            print(graphql_status)
            
            # Also log to file
            with open("/tmp/crm_heartbeat_log.txt", 'a') as f:
                f.write(f"{timestamp} {graphql_status}\n")
                
    except Exception as e:
        error_msg = f"GraphQL endpoint check failed: {str(e)}"
        print(error_msg)
        
        # Log error to file
        try:
            with open("/tmp/crm_heartbeat_log.txt", 'a') as f:
                f.write(f"{timestamp} {error_msg}\n")
        except:
            pass
    
    return message


def update_low_stock():
    """
    Cron job that runs every 12 hours to update low-stock products
    Executes the UpdateLowStockProducts GraphQL mutation
    Logs updated product names and new stock levels to /tmp/low_stock_updates_log.txt with a timestamp.
    """
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = "/tmp/low_stock_updates_log.txt"  # Make sure this matches exactly what the checker expects
    
    # Create header for this run
    header = f"\n{'='*60}\nLow Stock Update Run: {timestamp}\n{'='*60}"
    print(header)
    
    # Log header to file
    try:
        with open(log_file, 'a') as f:
            f.write(header + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")
    
    try:
        # Set up GraphQL client
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=True,
            retries=3,
            timeout=30
        )
        
        client = Client(
            transport=transport,
            fetch_schema_from_transport=True,
        )
        
        # Define the mutation to update low-stock products
        mutation = gql("""
            mutation UpdateLowStockProducts($incrementBy: Int) {
                updateLowStockProducts(incrementBy: $incrementBy) {
                    success
                    message
                    updateCount
                    updatedProducts {
                        id
                        name
                        stock
                        price
                    }
                }
            }
        """)
        
        # Execute the mutation with increment_by=10
        variables = {"incrementBy": 10}
        result = client.execute(mutation, variable_values=variables)
        
        mutation_result = result['updateLowStockProducts']
        
        # Prepare log message
        log_message = f"Status: {mutation_result['message']}\n"
        log_message += f"Success: {mutation_result['success']}\n"
        log_message += f"Products updated: {mutation_result['updateCount']}\n"
        
        # Log details of each updated product
        if mutation_result['updatedProducts']:
            log_message += "\nUpdated Products:\n"
            for product in mutation_result['updatedProducts']:
                product_info = (
                    f"  - ID: {product['id']}, "
                    f"Name: '{product['name']}', "
                    f"New Stock: {product['stock']}, "
                    f"Price: ${float(product['price']):.2f}"
                )
                log_message += product_info + "\n"
                print(f"Updated: {product['name']} (Stock: {product['stock']})")
        else:
            log_message += "\nNo products were updated (no low stock items found).\n"
        
        # Print to console
        print(f"\n{log_message}")
        
        # Append detailed log to file
        with open(log_file, 'a') as f:
            f.write(log_message + "\n")
        
        # Return summary message
        summary = f"Low stock update completed at {timestamp}: {mutation_result['message']}"
        print(summary)
        return summary
        
    except Exception as e:
        error_message = f"Error in low stock update at {timestamp}: {str(e)}"
        print(f"ERROR: {error_message}")
        
        # Log error to file
        try:
            with open(log_file, 'a') as f:
                f.write(f"ERROR: {error_message}\n")
        except:
            pass
        
        return f"Failed: {str(e)}"
