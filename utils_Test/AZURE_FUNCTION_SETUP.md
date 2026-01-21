# Azure Function Setup Guide

This guide explains how to create and deploy the Azure Function that processes IoT Hub messages and stores them in PostgreSQL.

## Prerequisites

- Azure subscription
- Azure IoT Hub already configured
- Azure Database for PostgreSQL created
- Azure CLI installed (optional but recommended)
- VS Code with Azure Functions extension (recommended)

---

## Step 1: Create Azure Function App

### Option A: Using Azure Portal

1. Go to **Azure Portal** → **Create a resource**
2. Search for "Function App" → Click **Create**
3. Configure:
   - **Subscription**: Your subscription
   - **Resource Group**: Same as IoT Hub (or create new)
   - **Function App name**: `nexus-rfid-processor` (must be globally unique)
   - **Runtime stack**: Python
   - **Version**: 3.9 or higher
   - **Region**: Same as IoT Hub (for lower latency)
   - **Operating System**: Linux
   - **Plan type**: Consumption (Serverless) or Premium
4. Click **Review + create** → **Create**

### Option B: Using Azure CLI

```bash
# Variables
RESOURCE_GROUP="nexus-rfid-rg"
LOCATION="eastus"
STORAGE_ACCOUNT="nexusrfidstorage"
FUNCTION_APP="nexus-rfid-processor"

# Create storage account (required for Functions)
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create Function App
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --storage-account $STORAGE_ACCOUNT \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --os-type Linux \
  --consumption-plan-location $LOCATION
```

---

## Step 2: Create Function Code

Create a new directory for your Function:

```bash
mkdir nexus-iot-function
cd nexus-iot-function
```

### File: `function_app.py`

```python
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import azure.functions as func
import os
from datetime import datetime

app = func.FunctionApp()

# PostgreSQL connection parameters from environment variables
DB_HOST = os.environ.get("POSTGRES_HOST")
DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")

def get_db_connection():
    """Create PostgreSQL connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            connect_timeout=10
        )
        return conn
    except psycopg2.Error as e:
        logging.error(f"Database connection failed: {e}")
        raise

@app.event_hub_message_trigger(
    arg_name="azeventhub",
    event_hub_name="<REPLACE_WITH_IOT_HUB_NAME>",
    connection="IoTHubConnectionString"
)
def process_iot_scan(azeventhub: func.EventHubEvent):
    """
    Process RFID scan messages from IoT Hub and store in PostgreSQL
    """
    try:
        # Parse message body
        message_body = azeventhub.get_body().decode('utf-8')
        scan_data = json.loads(message_body)
        
        logging.info(f"Processing scan: {scan_data.get('tagName')}")
        
        # Extract IoT Hub system properties
        iothub_enqueued_time = azeventhub.enqueued_time
        
        # Get device info from message
        device_info = scan_data.get('deviceInfo', {})
        
        # Insert into PostgreSQL
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                insert_query = """
                    INSERT INTO rfid_scans (
                        site_id, tag_name, latitude, longitude, speed,
                        device_id, antenna, bearing, rssi, is_processed,
                        device_metadata, iothub_enqueued_time, scan_timestamp
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                """
                
                # Prepare device metadata JSON
                metadata_json = json.dumps({
                    'siteName': device_info.get('siteName'),
                    'truckNumber': device_info.get('truckNumber'),
                    'deviceSerial': device_info.get('deviceSerial'),
                    'registrationId': device_info.get('registrationId')
                })
                
                # Prepare values for insertion
                values = (
                    scan_data.get('siteId'),
                    scan_data.get('tagName'),
                    float(scan_data.get('latitude', 0)),
                    float(scan_data.get('longitude', 0)),
                    int(scan_data.get('speed', 0)),
                    scan_data.get('deviceId'),
                    int(scan_data.get('antenna', 1)),
                    scan_data.get('barrier', '0'),
                    scan_data.get('rssi', '0'),
                    scan_data.get('isProcess', True),
                    metadata_json,
                    iothub_enqueued_time,
                    scan_data.get('metadata', {}).get('timestamp')
                )
                
                cursor.execute(insert_query, values)
                conn.commit()
                
                logging.info(f"✓ Successfully stored scan: {scan_data.get('tagName')}")
                
        finally:
            conn.close()
            
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in message: {e}")
        logging.error(f"Message body: {message_body}")
    except psycopg2.Error as e:
        logging.error(f"Database error: {e}")
        logging.error(f"Scan data: {scan_data}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        logging.error(f"Message: {message_body}")
        raise
```

### File: `requirements.txt`

```txt
azure-functions
psycopg2-binary
```

### File: `host.json`

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 20
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
```

---

## Step 3: Configure PostgreSQL Database

### Create Database Schema

Connect to your Azure PostgreSQL database and run:

```sql
-- Create table
CREATE TABLE rfid_scans (
    id BIGSERIAL PRIMARY KEY,
    
    -- Scan data
    site_id UUID NOT NULL,
    tag_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    speed INTEGER,
    device_id VARCHAR(100),
    antenna INTEGER,
    bearing VARCHAR(20),
    rssi VARCHAR(20),
    is_processed BOOLEAN DEFAULT TRUE,
    
    -- Device metadata
    device_metadata JSONB,
    
    -- Timestamps
    scan_timestamp BIGINT,  -- Original UTC microseconds from RFID reader
    iothub_enqueued_time TIMESTAMP,
    received_timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_rfid_scans_tag_name ON rfid_scans(tag_name);
CREATE INDEX idx_rfid_scans_site_id ON rfid_scans(site_id);
CREATE INDEX idx_rfid_scans_device_id ON rfid_scans(device_id);
CREATE INDEX idx_rfid_scans_received_timestamp ON rfid_scans(received_timestamp DESC);
CREATE INDEX idx_rfid_scans_metadata ON rfid_scans USING GIN (device_metadata);

-- Create view for easy querying
CREATE VIEW rfid_scans_enriched AS
SELECT 
    rs.*,
    rs.device_metadata->>'siteName' as site_name,
    rs.device_metadata->>'truckNumber' as truck_number,
    rs.device_metadata->>'deviceSerial' as device_serial,
    rs.device_metadata->>'registrationId' as registration_id
FROM rfid_scans rs;
```

### Configure PostgreSQL Firewall

Allow Azure services to access your PostgreSQL:

1. Go to **Azure Portal** → Your PostgreSQL server
2. Navigate to **Connection security**
3. Set **Allow access to Azure services**: ON
4. Add your Function App's outbound IP addresses (if using dedicated plan)
5. Click **Save**

---

## Step 4: Get IoT Hub Connection String

You need the Event Hub-compatible connection string from IoT Hub:

### Using Azure Portal:

1. Go to **Azure Portal** → Your IoT Hub
2. Navigate to **Built-in endpoints**
3. Copy the **Event Hub-compatible endpoint** connection string
4. It should look like:
   ```
   Endpoint=sb://ihsuprodblres001dednamespace.servicebus.windows.net/;SharedAccessKeyName=iothubowner;SharedAccessKey=xxxxx;EntityPath=iothub-ehub-your-hub-name
   ```

### Using Azure CLI:

```bash
az iot hub connection-string show \
  --hub-name <your-iot-hub-name> \
  --policy-name service \
  --resource-group <your-resource-group>
```

---

## Step 5: Configure Function App Settings

Add configuration to your Function App:

### Using Azure Portal:

1. Go to **Azure Portal** → Your Function App
2. Navigate to **Configuration** → **Application settings**
3. Add the following settings:

| Name | Value |
|------|-------|
| `IoTHubConnectionString` | Your IoT Hub Event Hub-compatible connection string |
| `POSTGRES_HOST` | `your-postgres-server.postgres.database.azure.com` |
| `POSTGRES_DB` | `your-database-name` |
| `POSTGRES_USER` | `your-admin-username@your-postgres-server` |
| `POSTGRES_PASSWORD` | `your-password` |
| `POSTGRES_PORT` | `5432` |

4. Click **Save**

### Using Azure CLI:

```bash
FUNCTION_APP="nexus-rfid-processor"
RESOURCE_GROUP="nexus-rfid-rg"

# IoT Hub connection string
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings IoTHubConnectionString="<your-connection-string>"

# PostgreSQL settings
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings \
    POSTGRES_HOST="<your-server>.postgres.database.azure.com" \
    POSTGRES_DB="<database-name>" \
    POSTGRES_USER="<admin-user>@<server-name>" \
    POSTGRES_PASSWORD="<password>" \
    POSTGRES_PORT="5432"
```

---

## Step 6: Deploy Function

### Option A: Using VS Code (Recommended)

1. Install **Azure Functions** extension in VS Code
2. Open your function folder in VS Code
3. Click Azure icon in sidebar
4. Sign in to Azure
5. Right-click your Function App → **Deploy to Function App**
6. Confirm deployment

### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Deploy function
cd nexus-iot-function
func azure functionapp publish nexus-rfid-processor
```

### Option C: Using Azure Portal (Manual)

1. Zip your function files:
   ```bash
   zip -r function.zip function_app.py requirements.txt host.json
   ```
2. Go to **Azure Portal** → Your Function App
3. Navigate to **Advanced Tools (Kudu)** → **Go**
4. Click **Tools** → **Zip Push Deploy**
5. Upload your `function.zip`

---

## Step 7: Verify Deployment

### Check Function Status

1. Go to **Azure Portal** → Your Function App
2. Navigate to **Functions**
3. You should see `process_iot_scan` function
4. Click on it → **Monitor**

### Test with Sample Data

Send a test message from Raspberry Pi:

```bash
python3 utils_Test/test_iot_publisher.py 1
```

### Check Logs

1. In Function App → **Monitor** → **Logs**
2. You should see:
   ```
   Processing scan: E20034120B1B017012345678
   ✓ Successfully stored scan: E20034120B1B017012345678
   ```

### Verify PostgreSQL

Connect to your PostgreSQL database and query:

```sql
SELECT * FROM rfid_scans_enriched 
ORDER BY received_timestamp DESC 
LIMIT 5;
```

---

## Troubleshooting

### Function Not Triggering

**Check:**
1. IoT Hub connection string is correct
2. Event Hub-compatible name matches in `function_app.py`
3. Function App is running (not stopped)
4. Check Application Insights for errors

**Fix Event Hub Name:**
In `function_app.py`, replace:
```python
event_hub_name="<REPLACE_WITH_IOT_HUB_NAME>"
```
With the actual Event Hub-compatible name from IoT Hub built-in endpoint.

### Database Connection Errors

**Error: "could not connect to server"**
- Check PostgreSQL firewall rules
- Verify connection string values
- Test connection from Azure Portal Cloud Shell

**Error: "authentication failed"**
- Verify username format: `user@servername`
- Check password is correct
- Ensure user has permissions on database

### Import Errors

**Error: "No module named 'psycopg2'"**
- Ensure `requirements.txt` includes `psycopg2-binary`
- Redeploy function

---

## Monitoring and Scaling

### Application Insights

Your Function App automatically logs to Application Insights:

1. Go to **Function App** → **Application Insights**
2. View **Live Metrics** for real-time monitoring
3. Use **Logs** (Kudu) for detailed query analysis

### Performance

- **Consumption Plan**: Auto-scales based on load
- **Premium Plan**: Pre-warmed instances, no cold start
- Monitor **Execution Count** and **Execution Duration** metrics

### Alerts

Set up alerts for:
- Failed executions
- Database connection failures
- High latency

---

## Next Steps

1. **Test end-to-end flow** from Raspberry Pi to PostgreSQL
2. **Monitor performance** during initial deployment
3. **Set up alerts** for failures
4. **Create dashboard** in Azure Portal or PowerBI
5. **Implement data retention** policy (optional)

---

## Cost Optimization

- Use **Consumption Plan** for low/variable traffic
- Consider **Premium Plan** if cold starts are an issue
- Set up **auto-pause** for dev/test environments
- Monitor **execution count** to estimate costs

Consumption Plan Pricing:
- First 400,000 GB-s free per month
- $0.20 per million executions (after first 1M free)
- Very cost-effective for IoT scenarios

---

## Security Best Practices

1. **Use Managed Identity** instead of connection strings (advanced)
2. **Store secrets** in Azure Key Vault
3. **Enable SSL** for PostgreSQL connections
4. **Restrict network access** to Function App
5. **Monitor access logs** regularly
