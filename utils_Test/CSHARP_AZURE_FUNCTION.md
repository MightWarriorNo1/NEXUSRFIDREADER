# C# Azure Function Setup Guide

This guide explains how to deploy the C# Azure Function that processes IoT Hub messages and stores them in PostgreSQL.

## Overview

The Azure Function uses:
- **Language**: C# (.NET 6 or higher)
- **Trigger**: IoT Hub EventHub trigger
- **Database**: Azure Database for PostgreSQL with Npgsql
- **Message Format**: JSON telemetry from RFID scanners

## Prerequisites

- Azure subscription
- Azure IoT Hub configured
- Azure Database for PostgreSQL created
- Visual Studio 2022 or VS Code with C# extension
- .NET 6.0 SDK or higher
- Azure Functions Core Tools v4

---

## Step 1: Create Azure Function App

### Using Azure Portal

1. Go to **Azure Portal** → **Create a resource**
2. Search for "Function App" → Click **Create**
3. Configure:
   - **Function App name**: `nexus-rfid-processor` (must be globally unique)
   - **Runtime stack**: .NET
   - **Version**: 6 (LTS) or higher
   - **Region**: Same as IoT Hub
   - **Operating System**: Windows (recommended for C#)
   - **Plan type**: Consumption (Serverless) or Premium
4. Click **Review + create** → **Create**

### Using Azure CLI

```bash
RESOURCE_GROUP="nexus-rfid-rg"
LOCATION="eastus"
STORAGE_ACCOUNT="nexusrfidstorage"
FUNCTION_APP="nexus-rfid-processor"

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Create Function App
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --storage-account $STORAGE_ACCOUNT \
  --runtime dotnet \
  --runtime-version 6 \
  --functions-version 4 \
  --os-type Windows \
  --consumption-plan-location $LOCATION
```

---

## Step 2: PostgreSQL Database Schema

Your existing C# function expects this schema:

```sql
-- Create Scans table
CREATE TABLE IF NOT EXISTS public."Scans" (
    "Id" UUID PRIMARY KEY,
    "TagName" VARCHAR(100) NOT NULL,
    "Latitude" DOUBLE PRECISION,
    "Longitude" DOUBLE PRECISION,
    "Speed" DOUBLE PRECISION,
    "DeviceId" VARCHAR(100),
    "SiteId" UUID NOT NULL,
    "IsProcess" BOOLEAN DEFAULT FALSE,
    "Antenna" VARCHAR(20),
    "IsDeleted" BOOLEAN DEFAULT FALSE,
    "CreatedOn" TIMESTAMP NOT NULL,
    "CreatedBy" UUID NOT NULL,
    "UpdatedOn" TIMESTAMP NULL,
    "UpdatedBy" UUID NULL,
    "Barrier" DOUBLE PRECISION,
    "Comment" TEXT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS "idx_Scans_TagName" ON public."Scans"("TagName");
CREATE INDEX IF NOT EXISTS "idx_Scans_SiteId" ON public."Scans"("SiteId");
CREATE INDEX IF NOT EXISTS "idx_Scans_DeviceId" ON public."Scans"("DeviceId");
CREATE INDEX IF NOT EXISTS "idx_Scans_CreatedOn" ON public."Scans"("CreatedOn" DESC);
CREATE INDEX IF NOT EXISTS "idx_Scans_IsDeleted" ON public."Scans"("IsDeleted");

-- View for easy querying (non-deleted scans)
CREATE OR REPLACE VIEW public."ActiveScans" AS
SELECT *
FROM public."Scans"
WHERE "IsDeleted" = FALSE
ORDER BY "CreatedOn" DESC;
```

---

## Step 3: Create C# Azure Function Project

### Using Visual Studio 2022

1. Open Visual Studio → **Create a new project**
2. Search for "Azure Functions" → Select template
3. Project name: `NexusIoTFunction`
4. Configure:
   - **Functions worker**: .NET 6.0 LTS (or higher)
   - **Function type**: Event Hub trigger
   - **Storage account**: Use emulator for local development
5. Click **Create**

### Using VS Code / Command Line

```bash
# Create new Functions project
func init NexusIoTFunction --dotnet

cd NexusIoTFunction

# Add IoT Hub trigger function
func new --name IotHubToPostgres --template "EventHubTrigger"
```

---

## Step 4: Implement the C# Function

### File: `IotHubToPostgres.cs`

Your existing code (with minor enhancements):

```csharp
using System;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Azure.EventHubs;
using Microsoft.Azure.WebJobs;
using Microsoft.Extensions.Logging;
using Npgsql;
using Newtonsoft.Json.Linq;

public static class IotHubToPostgres
{
    private static readonly string PostgresConn =
        Environment.GetEnvironmentVariable("POSTGRES_CONN");

    // IMPORTANT: Use your own consumer group
    [FunctionName("IotHubToPostgres")]
    public static async Task Run(
        [IoTHubTrigger("messages/events",
            Connection = "IOTHUB_CONNECTION",
            ConsumerGroup = "func-cg-nexuslocate")] EventData[] events,
        ILogger log)
    {
        if (events == null || events.Length == 0) return;

        await using var conn = new NpgsqlConnection(PostgresConn);
        await conn.OpenAsync();

        const string sql = @"
            INSERT INTO public.""Scans""
            (""Id"", ""TagName"", ""Latitude"", ""Longitude"", ""Speed"",
             ""DeviceId"", ""SiteId"", ""IsProcess"", ""Antenna"", ""IsDeleted"",
             ""CreatedOn"", ""CreatedBy"", ""UpdatedOn"", ""UpdatedBy"",
             ""Barrier"", ""Comment"")
            VALUES
            (@Id, @TagName, @Latitude, @Longitude, @Speed,
             @DeviceId, @SiteId, @IsProcess, @Antenna, @IsDeleted,
             @CreatedOn, @CreatedBy, NULL, NULL,
             @Barrier, @Comment);
        ";

        int inserted = 0;

        foreach (var e in events)
        {
            try
            {
                string body = Encoding.UTF8.GetString(e.Body.Array, e.Body.Offset, e.Body.Count);
                var json = JObject.Parse(body);

                // Accept either camelCase or PascalCase
                string tagName  = (string)(json["tagName"] ?? json["TagName"] ?? json["epc"]) ?? "UNKNOWN";
                string deviceId = (string)(json["deviceId"] ?? json["DeviceId"]) ?? "UNKNOWN";
                string antenna  = (string)(json["antenna"] ?? json["Antenna"]) ?? "UNKNOWN";

                double latitude  = (double?)(json["latitude"] ?? json["Latitude"]) ?? 0.0;
                double longitude = (double?)(json["longitude"] ?? json["Longitude"]) ?? 0.0;
                double speed     = (double?)(json["speed"] ?? json["Speed"]) ?? 0.0;
                double barrier   = (double?)(json["barrier"] ?? json["Barrier"]) ?? 0.0;

                // SiteId required in your schema
                Guid siteId = Guid.Empty;
                var siteStr = (string)(json["siteId"] ?? json["SiteId"]);
                if (!string.IsNullOrEmpty(siteStr) && !Guid.TryParse(siteStr, out siteId))
                {
                    log.LogWarning($"Invalid siteId format: {siteStr}, using Empty Guid");
                    siteId = Guid.Empty;
                }

                // CreatedBy - use a fixed system user ID
                Guid createdBy = Guid.Parse("11111111-1111-1111-1111-111111111111");

                string comment = (string)(json["comment"] ?? json["Comment"]) ?? null;

                await using var cmd = new NpgsqlCommand(sql, conn);
                cmd.Parameters.AddWithValue("@Id", Guid.NewGuid());
                cmd.Parameters.AddWithValue("@TagName", tagName);
                cmd.Parameters.AddWithValue("@Latitude", latitude);
                cmd.Parameters.AddWithValue("@Longitude", longitude);
                cmd.Parameters.AddWithValue("@Speed", speed);
                cmd.Parameters.AddWithValue("@DeviceId", deviceId);
                cmd.Parameters.AddWithValue("@SiteId", siteId);
                cmd.Parameters.AddWithValue("@IsProcess", false);
                cmd.Parameters.AddWithValue("@Antenna", antenna);
                cmd.Parameters.AddWithValue("@IsDeleted", false);
                cmd.Parameters.AddWithValue("@CreatedOn", DateTime.UtcNow);
                cmd.Parameters.AddWithValue("@CreatedBy", createdBy);
                cmd.Parameters.AddWithValue("@Barrier", barrier);
                cmd.Parameters.AddWithValue("@Comment", (object?)comment ?? DBNull.Value);

                await cmd.ExecuteNonQueryAsync();
                inserted++;
            }
            catch (Exception ex)
            {
                log.LogError(ex, "Failed processing IoT message (skipped).");
            }
        }

        log.LogInformation($"Inserted {inserted} rows into public.\"Scans\".");
    }
}
```

### File: `NexusIoTFunction.csproj`

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <AzureFunctionsVersion>v4</AzureFunctionsVersion>
  </PropertyGroup>
  
  <ItemGroup>
    <PackageReference Include="Microsoft.Azure.WebJobs.Extensions.EventHubs" Version="5.5.0" />
    <PackageReference Include="Microsoft.NET.Sdk.Functions" Version="4.2.0" />
    <PackageReference Include="Npgsql" Version="7.0.6" />
    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
  </ItemGroup>
  
  <ItemGroup>
    <None Update="host.json">
      <CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>
    </None>
    <None Update="local.settings.json">
      <CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>
      <CopyToPublishOutput>false</CopyToPublishOutput>
    </None>
  </ItemGroup>
</Project>
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
  "extensions": {
    "eventHubs": {
      "batchCheckpointFrequency": 5,
      "maxEventBatchSize": 100,
      "prefetchCount": 300
    }
  }
}
```

### File: `local.settings.json` (for local development)

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "dotnet",
    "IOTHUB_CONNECTION": "Endpoint=sb://your-iothub-events.servicebus.windows.net/;...",
    "POSTGRES_CONN": "Host=your-server.postgres.database.azure.com;Database=nexus;Username=admin;Password=yourpassword;SSL Mode=Require;"
  }
}
```

---

## Step 5: Get IoT Hub Connection String

You need the **Event Hub-compatible endpoint** connection string:

### Using Azure Portal

1. Go to **Azure Portal** → Your IoT Hub
2. Navigate to **Built-in endpoints**
3. Copy **Event Hub-compatible endpoint** connection string
4. Format:
   ```
   Endpoint=sb://ihsuprodXXXX.servicebus.windows.net/;SharedAccessKeyName=iothubowner;SharedAccessKey=xxxxx;EntityPath=your-hub-name
   ```

### Using Azure CLI

```bash
az iot hub connection-string show \
  --hub-name <your-iot-hub-name> \
  --policy-name service
```

---

## Step 6: Create IoT Hub Consumer Group

**IMPORTANT**: Create a dedicated consumer group for your function to avoid conflicts.

### Using Azure Portal

1. Go to **Azure Portal** → Your IoT Hub
2. Navigate to **Built-in endpoints**
3. Under **Consumer groups**, add: `func-cg-nexuslocate`
4. Click **Save**

### Using Azure CLI

```bash
az iot hub consumer-group create \
  --hub-name <your-iot-hub-name> \
  --name func-cg-nexuslocate \
  --event-hub-name <event-hub-compatible-name>
```

---

## Step 7: Configure Function App Settings

Add configuration settings to your deployed Function App:

### Using Azure Portal

1. Go to **Azure Portal** → Your Function App
2. Navigate to **Configuration** → **Application settings**
3. Add these settings:

| Name | Value |
|------|-------|
| `IOTHUB_CONNECTION` | Event Hub-compatible connection string from IoT Hub |
| `POSTGRES_CONN` | `Host=your-server.postgres.database.azure.com;Database=nexus;Username=admin;Password=yourpassword;SSL Mode=Require;` |

4. Click **Save** → **Continue**

### Using Azure CLI

```bash
FUNCTION_APP="nexus-rfid-processor"
RESOURCE_GROUP="nexus-rfid-rg"

# IoT Hub connection
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings IOTHUB_CONNECTION="<your-event-hub-connection-string>"

# PostgreSQL connection
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings POSTGRES_CONN="Host=<server>.postgres.database.azure.com;Database=nexus;Username=<user>;Password=<password>;SSL Mode=Require;"
```

---

## Step 8: Deploy Function

### Using Visual Studio 2022

1. Right-click project → **Publish**
2. Target: **Azure**
3. Specific target: **Azure Function App (Windows)**
4. Select your Function App
5. Click **Publish**

### Using VS Code

1. Install **Azure Functions** extension
2. Click Azure icon in sidebar
3. Sign in to Azure
4. Right-click your Function App → **Deploy to Function App**
5. Confirm deployment

### Using Azure Functions Core Tools

```bash
# Login to Azure
az login

# Publish function
cd NexusIoTFunction
func azure functionapp publish nexus-rfid-processor
```

---

## Step 9: Test End-to-End

### From Raspberry Pi

Run the test publisher to send data:

```bash
python3 utils_Test/test_iot_publisher.py 5
```

### Verify in Azure

1. **Function App Logs**:
   - Go to Function App → Monitor → Logs
   - Look for: `Inserted X rows into public."Scans".`

2. **PostgreSQL Database**:
   ```sql
   SELECT * FROM public."ActiveScans"
   ORDER BY "CreatedOn" DESC
   LIMIT 10;
   ```

Expected output:
- Tag names starting with "E20034120B1B..."
- SiteId: `019a9e1e-81ff-75ab-99fc-4115bb92fec6`
- DeviceId, Latitude, Longitude, Speed populated
- CreatedOn timestamps

---

## Step 10: Monitoring and Troubleshooting

### Enable Application Insights

1. Go to Function App → Application Insights → **Turn on**
2. Create new instance or use existing
3. View **Live Metrics** for real-time monitoring

### Check Logs

**Application Insights Query**:
```kusto
traces
| where timestamp > ago(1h)
| where message contains "Inserted"
| order by timestamp desc
```

**Function App Logs** (Log stream):
```bash
# In Azure Portal
Function App → Log stream
```

### Common Issues

**Function Not Triggering**

- Verify `IOTHUB_CONNECTION` is correct Event Hub-compatible endpoint
- Check consumer group exists: `func-cg-nexuslocate`
- Ensure Function App is running (not stopped)

**Database Connection Errors**

```
Npgsql.NpgsqlException: connection failed
```

**Solutions:**
- Check PostgreSQL firewall allows Azure services
- Verify connection string format
- Test connection from Azure Portal Cloud Shell:
  ```bash
  psql "Host=<server>.postgres.database.azure.com;Database=nexus;Username=<user>;Password=<pwd>;SSL Mode=Require;"
  ```

**Invalid SiteId**

```
Warning: Invalid siteId format: xxx, using Empty Guid
```

**Solution:**
- Ensure Raspberry Pi sends valid UUID format
- Check test data: `"siteId": "019a9e1e-81ff-75ab-99fc-4115bb92fec6"`

**Message Processing Errors**

Check function logs for:
```
Failed processing IoT message (skipped).
```

Enable detailed logging to see JSON parsing errors.

---

## Step 11: Performance Optimization

### Batch Settings

In `host.json`:
```json
{
  "extensions": {
    "eventHubs": {
      "batchCheckpointFrequency": 5,
      "maxEventBatchSize": 100,
      "prefetchCount": 300
    }
  }
}
```

### Connection Pooling

Npgsql automatically handles connection pooling. For high-throughput scenarios, consider:

```csharp
// Add to connection string
"Pooling=true;Maximum Pool Size=100;"
```

### Scale Out

For high message volume:
1. Go to Function App → **Scale out (App Service plan)**
2. Or use **Premium Plan** for pre-warmed instances

---

## Message Format Reference

Your C# function accepts JSON with flexible field names (camelCase or PascalCase):

```json
{
  "siteId": "019a9e1e-81ff-75ab-99fc-4115bb92fec6",
  "tagName": "E20034120B1B017012345678",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "speed": 15.0,
  "deviceId": "1000000012345678",
  "antenna": "1",
  "barrier": 270.0,
  "comment": null,
  "deviceInfo": {
    "registrationId": "1000000012345678",
    "siteName": "Lazer",
    "truckNumber": "0000000012345678"
  }
}
```

**Field Mappings:**
- `tagName` / `TagName` / `epc` → TagName (string)
- `deviceId` / `DeviceId` → DeviceId (string)
- `antenna` / `Antenna` → Antenna (string)
- `latitude` / `Latitude` → Latitude (double)
- `longitude` / `Longitude` → Longitude (double)
- `speed` / `Speed` → Speed (double)
- `barrier` / `Barrier` → Barrier (double, bearing/heading)
- `siteId` / `SiteId` → SiteId (UUID)
- `comment` / `Comment` → Comment (string, optional)

---

## Cost Estimates

**Consumption Plan Pricing:**
- Executions: First 1M free, then $0.20 per million
- Execution time: First 400,000 GB-s free, then $0.000016/GB-s
- Very cost-effective for IoT scenarios

**Typical Monthly Cost:**
- 100,000 messages/day: ~$5-10/month
- 1,000,000 messages/day: ~$30-50/month

---

## Security Best Practices

1. **Use Managed Identity** (advanced):
   - Enable system-assigned identity on Function App
   - Grant access to PostgreSQL without password

2. **Store Secrets in Key Vault**:
   - Move connection strings to Azure Key Vault
   - Reference in app settings: `@Microsoft.KeyVault(SecretUri=...)`

3. **Network Security**:
   - Use VNet integration for Function App
   - Private endpoints for PostgreSQL

4. **Monitoring**:
   - Set up alerts for failed executions
   - Monitor database connection pool
   - Track message processing latency

---

## Next Steps

1. ✅ Deploy C# Function to Azure
2. ✅ Test with Raspberry Pi test scripts
3. ✅ Verify data in PostgreSQL
4. ✅ Set up monitoring and alerts
5. ✅ Integrate into main RFID application
6. ✅ Deploy to production devices

---

## Support Resources

- [Azure Functions C# Developer Guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-dotnet-class-library)
- [Npgsql Documentation](https://www.npgsql.org/doc/)
- [Azure IoT Hub Routing](https://learn.microsoft.com/en-us/azure/iot-hub/iot-hub-devguide-messages-d2c)
