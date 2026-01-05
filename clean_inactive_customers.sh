#!/bin/bash

# =============================================================================
# clean_inactive_customers.sh - FINAL CLEAN VERSION
# Deletes customers with no orders in the last 365 days
# Logs cleanly to /tmp/customer_cleanup_log.txt
# =============================================================================

set -e

# --- Find project root ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

while [ ! -f "$PROJECT_ROOT/manage.py" ] && [ "$PROJECT_ROOT" != "/" ]; do
    PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
done

if [ ! -f "$PROJECT_ROOT/manage.py" ]; then
    echo "[ERROR] Could not find manage.py!" >&2
    exit 1
fi

echo "Project root found: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# --- Run cleanup: Use --no-startup to suppress all Django startup noise ---
# --- Only capture the final number from print(count) ---
DELETED_COUNT=$(python manage.py shell --no-startup << 'EOF' 2>/dev/null | tail -n 1
import datetime
from django.utils import timezone
from crm.models import Customer, Order

one_year_ago = timezone.now() - datetime.timedelta(days=365)

# Get active customer IDs (those with at least one order in last year)
active_ids = Order.objects.filter(order_date__gte=one_year_ago)\
                         .values_list('customer_id', flat=True)\
                         .distinct()

# Inactive customers: everyone else (including those with zero orders)
to_delete = Customer.objects.exclude(id__in=active_ids)

# Delete and print only the count
count, _ = to_delete.delete()
print(count)
EOF
)

# --- Use system time for timestamp (reliable in cron too) ---
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# --- Log cleanly ---
LOG_FILE="/tmp/customer_cleanup_log.txt"
echo "$TIMESTAMP: Deleted $DELETED_COUNT inactive customer(s)." >> "$LOG_FILE"

# --- Final clean output ---
echo "Cleanup complete. Deleted $DELETED_COUNT inactive customer(s)."
echo "Log written to: $LOG_FILE"
echo
echo "Recent log entries:"
tail -n 5 "$LOG_FILE" 2>/dev/null || echo "(Log file just created)"
