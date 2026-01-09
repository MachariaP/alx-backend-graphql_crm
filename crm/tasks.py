"""
Celery tasks for CRM application
"""

import os
import sys
from datetime import datetime
from celery import shared_task
from celery.utils.log import get_task_logger
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

logger = get_task_logger(__name__)

@shared_task(name="generate_crm_report")
def generate_crm_report():
    """
    Generate a weekly CRM report summarizing:
    - Total number of customers
    - Total number of orders
    - Total revenue (sum of total_amount from orders)
    
    Logs the report to /tmp/crm_report_log.txt with a timestamp
    """
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = "/tmp/crm_report_log.txt"
    
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
        
        # Define the query to fetch CRM statistics
        query = gql("""
            query GetCRMStatistics {
                # Get total number of customers
                allCustomers {
                    totalCount
                }
                
                # Get total number of orders
                allOrders {
                    totalCount
                    edges {
                        node {
                            totalAmount
                        }
                    }
                }
            }
        """)
        
        # Execute the query
        result = client.execute(query)
        
        # Extract data from GraphQL response
        total_customers = result.get('allCustomers', {}).get('totalCount', 0)
        orders_data = result.get('allOrders', {})
        total_orders = orders_data.get('totalCount', 0)
        
        # Calculate total revenue
        total_revenue = 0.0
        edges = orders_data.get('edges', [])
        for edge in edges:
            node = edge.get('node', {})
            total_amount = node.get('totalAmount', 0)
            if total_amount:
                try:
                    total_revenue += float(total_amount)
                except (ValueError, TypeError):
                    pass
        
        # Format the report
        report_message = (
            f"{timestamp} - Report: {total_customers} customers, "
            f"{total_orders} orders, ${total_revenue:.2f} revenue"
        )
        
        # Log to file
        with open(log_file, 'a') as f:
            f.write(report_message + "\n")
        
        # Also log to Celery logger
        logger.info(f"CRM report generated: {report_message}")
        
        print(f"CRM Report: {report_message}")
        
        return {
            'timestamp': timestamp,
            'total_customers': total_customers,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'status': 'success'
        }
        
    except Exception as e:
        error_message = f"{timestamp} - Error generating CRM report: {str(e)}"
        
        # Log error to file
        try:
            with open(log_file, 'a') as f:
                f.write(error_message + "\n")
        except:
            pass
        
        logger.error(error_message)
        print(error_message)
        
        return {
            'timestamp': timestamp,
            'error': str(e),
            'status': 'failed'
        }
