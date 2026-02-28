import boto3
import os
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    retention_days = int(os.environ.get('RETENTION_DAYS', 365))
    cutoff_date = datetime.now(timezone.utc) - relativedelta(days=retention_days)
    
    print(f"Starting snapshot cleanup. Retention: {retention_days} days. Cutoff date: {cutoff_date}")
    
    deleted_count = 0
    error_count = 0
    
    try:
        # Get all snapshots owned by this account
        paginator = ec2.get_paginator('describe_snapshots')
        page_iterator = paginator.paginate(OwnerIds=['self'])
        
        for page in page_iterator:
            for snapshot in page['Snapshots']:
                snapshot_id = snapshot['SnapshotId']
                start_time = snapshot['StartTime']
                
                # Check if snapshot is older than retention period
                if start_time < cutoff_date:
                    try:
                        print(f"Deleting snapshot: {snapshot_id} (Created: {start_time})")
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting snapshot {snapshot_id}: {str(e)}")
                        error_count += 1
        
        print(f"Cleanup complete. Deleted: {deleted_count}, Errors: {error_count}")
        
        return {
            'statusCode': 200,
            'body': {
                'deleted': deleted_count,
                'errors': error_count,
                'retention_days': retention_days
            }
        }
        
    except Exception as e:
        print(f"Fatal error during snapshot cleanup: {str(e)}")
        raise
