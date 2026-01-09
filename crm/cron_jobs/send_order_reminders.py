#!/usr/bin/env python3
"""
Order Reminder Script
Sends reminders for pending orders from the last 7 days.
Run daily via cron job.
"""

import sys
import os
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import logging

# Add parent directory to path to allow imports from crm module if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
log_file = "/tmp/order_reminders_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_pending_orders():
    """Fetch pending orders from the last 7 days using GraphQL"""
    
    # Calculate date 7 days ago
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # GraphQL query to get pending orders from the last 7 days
    query = gql("""
    query GetPendingOrders($sinceDate: String!) {
        orders(
            where: {
                order_date: {gte: $sinceDate},
                status: {eq: "pending"}
            },
            orderBy: {order_date: DESC}
        ) {
            id
            customer_email
            order_date
            status
            total_amount
            customer {
                id
                name
                email
            }
        }
    }
    """)
    
    # Set up GraphQL client
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=True,
        retries=3,
    )
    
    client = Client(
        transport=transport,
        fetch_schema_from_transport=False,
    )
    
    try:
        # Execute the query
        variables = {"sinceDate": seven_days_ago}
        result = client.execute(query, variable_values=variables)
        
        return result.get('orders', [])
        
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        return []

def send_order_reminders():
    """Main function to process order reminders"""
    
    logger.info("=" * 50)
    logger.info("Starting order reminder processing...")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get pending orders
    orders = get_pending_orders()
    
    if not orders:
        logger.info("No pending orders found from the last 7 days.")
        return
    
    # Log each order
    for order in orders:
        order_id = order.get('id', 'N/A')
        customer_email = order.get('customer_email', 'N/A')
        
        # If customer_email is not directly on order, try to get from customer object
        if customer_email == 'N/A' and order.get('customer'):
            customer_email = order.get('customer', {}).get('email', 'N/A')
        
        # Get order date for additional info
        order_date = order.get('order_date', 'N/A')
        status = order.get('status', 'N/A')
        
        logger.info(f"Order ID: {order_id}, "
                   f"Customer Email: {customer_email}, "
                   f"Order Date: {order_date}, "
                   f"Status: {status}")
    
    logger.info(f"Total pending orders: {len(orders)}")
    logger.info("Order reminder processing completed.")
    logger.info("=" * 50)
    
    # Print to console (for cron job logs)
    print("Order reminders processed!")

if __name__ == "__main__":
    # Add a header to the log file
    with open(log_file, 'a') as f:
        f.write("\n" + "="*60 + "\n")
        f.write(f"Order Reminder Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n")
    
    try:
        send_order_reminders()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user.")
        print("Script interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)
