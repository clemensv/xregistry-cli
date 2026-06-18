# Using RabbitMQ with AMQP 1.0

This guide explains how to use RabbitMQ with the AMQP 1.0 protocol for the xRegistry CLI generated code.

## Overview

RabbitMQ's AMQP 1.0 support differs by version:

- **RabbitMQ 4.0+**: Native AMQP 1.0 support (no plugin required)
- **RabbitMQ 3.8.0 - 3.x**: AMQP 1.0 via plugin (`rabbitmq_amqp1_0`)

The xRegistry CLI generates AMQP 1.0 client code that works with any AMQP 1.0 compliant broker, including:

- **Apache ActiveMQ Artemis** (native AMQP 1.0 support)
- **Apache Qpid** (native AMQP 1.0 support)
- **Azure Service Bus** (native AMQP 1.0 support)
- **RabbitMQ 4.0+** (native AMQP 1.0 support)
- **RabbitMQ 3.8.0 - 3.x** (via AMQP 1.0 plugin)

## Why Use AMQP 1.0 with RabbitMQ?

While RabbitMQ's native AMQP 0.9.1 protocol is mature and widely used, AMQP 1.0 offers several advantages:

- **Standardization**: AMQP 1.0 is an OASIS and ISO/IEC standard (ISO/IEC 19464)
- **Interoperability**: Works across different brokers without protocol-specific code
- **Modern features**: Better support for flow control, message delivery guarantees, and link management
- **Cloud compatibility**: Native protocol for Azure Service Bus and other cloud messaging services

## Prerequisites

### RabbitMQ 4.0 and Later

- RabbitMQ 4.0 or later
- No additional setup required - AMQP 1.0 is natively supported

### RabbitMQ 3.8.0 to 3.x

- RabbitMQ 3.8.0 or later
- Admin access to enable the AMQP 1.0 plugin

## Enabling AMQP 1.0 Support

### RabbitMQ 4.0+: Native Support (Recommended)

RabbitMQ 4.0 and later versions include **native AMQP 1.0 support** out of the box. No plugin installation or configuration is needed.

**Using Docker with RabbitMQ 4.0+**:

```bash
docker run -d \
  --name rabbitmq-amqp \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:4-management
```

**Verify AMQP 1.0 is available**:
```bash
# Check that port 5672 is listening (AMQP 1.0 and 0.9.1 share this port)
docker exec rabbitmq-amqp rabbitmqctl status
```

### RabbitMQ 3.x: Plugin Installation

### RabbitMQ 3.x: Plugin Installation

For RabbitMQ versions 3.8.0 through 3.x, you need to enable the AMQP 1.0 plugin.

#### On a Local RabbitMQ Installation

1. **Enable the plugin**:
   ```bash
   rabbitmq-plugins enable rabbitmq_amqp1_0
   ```

2. **Restart RabbitMQ** (if needed):
   ```bash
   # Linux/macOS
   sudo systemctl restart rabbitmq-server
   
   # Or using rabbitmqctl
   rabbitmqctl stop_app
   rabbitmqctl start_app
   ```

3. **Verify the plugin is enabled**:
   ```bash
   rabbitmq-plugins list
   ```
   
   You should see:
   ```
   [E*] rabbitmq_amqp1_0
   ```

#### Using Docker with RabbitMQ 3.x

```bash
docker run -d \
  --name rabbitmq-amqp \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_PLUGINS=rabbitmq_amqp1_0 \
  rabbitmq:3-management
```

**Port mappings**:
- `5672`: AMQP 1.0 port (and AMQP 0.9.1)
- `15672`: Management UI (optional, for monitoring)

**Verify the plugin**:
```bash
docker exec rabbitmq-amqp rabbitmq-plugins list
```

#### Using Docker Compose with RabbitMQ 3.x

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  rabbitmq:
    image: rabbitmq:3-management
    container_name: rabbitmq-amqp
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
      - RABBITMQ_PLUGINS=rabbitmq_amqp1_0
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Start the service:
```bash
docker-compose up -d
```

### Docker Compose Examples

#### RabbitMQ 4.0+ (Recommended)

Create a `docker-compose.yml` file for RabbitMQ 4.0+:

```yaml
version: '3.8'
services:
  rabbitmq:
    image: rabbitmq:4-management
    container_name: rabbitmq-amqp
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

#### RabbitMQ 3.x with Plugin

For RabbitMQ 3.x, the plugin must be explicitly enabled:

```yaml
version: '3.8'
services:
  rabbitmq:
    image: rabbitmq:3-management
    container_name: rabbitmq-amqp
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
      - RABBITMQ_PLUGINS=rabbitmq_amqp1_0
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Kubernetes Deployments

#### RabbitMQ 4.0+ (Recommended)

Example Kubernetes deployment with native AMQP 1.0 support:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rabbitmq-amqp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rabbitmq
  template:
    metadata:
      labels:
        app: rabbitmq
    spec:
      containers:
      - name: rabbitmq
        image: rabbitmq:4-management
        ports:
        - containerPort: 5672
          name: amqp
        - containerPort: 15672
          name: management
        env:
        - name: RABBITMQ_DEFAULT_USER
          value: "guest"
        - name: RABBITMQ_DEFAULT_PASS
          value: "guest"
---
apiVersion: v1
kind: Service
metadata:
  name: rabbitmq-amqp
spec:
  selector:
    app: rabbitmq
  ports:
  - name: amqp
    port: 5672
    targetPort: 5672
  - name: management
    port: 15672
    targetPort: 15672
```

#### RabbitMQ 3.x with Plugin

Example Kubernetes deployment for RabbitMQ 3.x with AMQP 1.0 plugin:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rabbitmq-amqp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rabbitmq
  template:
    metadata:
      labels:
        app: rabbitmq
    spec:
      containers:
      - name: rabbitmq
        image: rabbitmq:3-management
        ports:
        - containerPort: 5672
          name: amqp
        - containerPort: 15672
          name: management
        env:
        - name: RABBITMQ_DEFAULT_USER
          value: "guest"
        - name: RABBITMQ_DEFAULT_PASS
          value: "guest"
        - name: RABBITMQ_PLUGINS
          value: "rabbitmq_amqp1_0"
---
apiVersion: v1
kind: Service
metadata:
  name: rabbitmq-amqp
spec:
  selector:
    app: rabbitmq
  ports:
  - name: amqp
    port: 5672
    targetPort: 5672
  - name: management
    port: 15672
    targetPort: 15672
```

## Connection Configuration

### Connection String Format

The AMQP 1.0 connection string for RabbitMQ follows the standard format:

```
amqp://[username[:password]@]host[:port][/vhost]
```

**Examples**:
- `amqp://localhost:5672` - Local RabbitMQ with default credentials
- `amqp://guest:guest@localhost:5672` - With explicit credentials
- `amqp://user:pass@rabbitmq.example.com:5672/%2Fmyvhost` - With virtual host (URL-encoded)

**Note**: The default virtual host `/` must be URL-encoded as `%2F` in connection strings.

### Java Connection Example

```java
import java.net.URI;
import java.util.List;

// Create AMQP 1.0 connection to RabbitMQ
URI brokerUrl = new URI("amqp://guest:guest@localhost:5672");
PlainEndpointCredential credential = new PlainEndpointCredential("guest", "guest");

Map<String, String> options = new HashMap<>();
options.put("node", "myqueue");

EventProducer producer = EventProducer.createProducer(
    credential,
    options,
    List.of(brokerUrl)
);
```

### C# Connection Example

```csharp
using System;

// Create AMQP 1.0 connection to RabbitMQ
var brokerUrl = new Uri("amqp://guest:guest@localhost:5672");
var credential = new PlainEndpointCredential("guest", "guest");

var options = new Dictionary<string, string>
{
    ["node"] = "myqueue"
};

var producer = EventProducer.CreateProducer(
    credential,
    options,
    new[] { brokerUrl }
);
```

### Python Connection Example

```python
# Create AMQP 1.0 connection to RabbitMQ
broker_url = "amqp://guest:guest@localhost:5672"

producer = EventProducer(
    host="localhost",
    port=5672,
    address="myqueue",
    username="guest",
    password="guest"
)
```

### TypeScript/JavaScript Connection Example

```typescript
import * as rhea from 'rhea';

// Create AMQP 1.0 connection to RabbitMQ
const connection = rhea.create_connection({
    host: 'localhost',
    port: 5672,
    username: 'guest',
    password: 'guest'
});

const sender = connection.open_sender({
    target: { address: 'myqueue' }
});
```

## Queue and Exchange Configuration

### Creating Queues

RabbitMQ automatically creates queues when messages are sent to them with AMQP 1.0. However, you can pre-create queues using the RabbitMQ Management UI or CLI:

```bash
# Using rabbitmqadmin (requires rabbitmq_management plugin)
rabbitmqadmin declare queue name=myqueue durable=true

# Using rabbitmqctl
rabbitmqctl add_queue myqueue
```

### Virtual Hosts

RabbitMQ supports virtual hosts for multi-tenancy. To use a specific virtual host:

1. **Create a virtual host**:
   ```bash
   rabbitmqctl add_vhost myvhost
   rabbitmqctl set_permissions -p myvhost guest ".*" ".*" ".*"
   ```

2. **Connect with virtual host**:
   ```java
   // URL-encode the vhost name
   URI brokerUrl = new URI("amqp://guest:guest@localhost:5672/%2Fmyvhost");
   ```

## Key Differences: AMQP 0.9.1 vs AMQP 1.0

Understanding the differences helps when working with RabbitMQ's AMQP 1.0 plugin:

| Feature | AMQP 0.9.1 (Native) | AMQP 1.0 (Plugin) |
|---------|---------------------|-------------------|
| **Exchange Types** | Direct, Topic, Fanout, Headers | Mapped to queues and topics |
| **Bindings** | Explicit bindings required | Simplified routing |
| **Message Properties** | Protocol-specific | Standardized message format |
| **Flow Control** | Basic | Advanced link-level flow control |
| **Transactions** | Supported | Supported via transactional sessions |

### Routing in AMQP 1.0

AMQP 1.0 uses a simplified routing model compared to AMQP 0.9.1:

- **Direct routing**: Messages are sent directly to queue names
- **No explicit exchanges**: The AMQP 1.0 plugin maps addresses to RabbitMQ queues
- **Topic patterns**: Can be simulated using RabbitMQ's topic exchanges with proper configuration

## Testing Your Setup

### Verify Plugin is Working

1. **Check RabbitMQ logs**:
   ```bash
   docker logs rabbitmq-amqp
   ```
   
   Look for:
   ```
   Starting plugin rabbitmq_amqp1_0
   ```

2. **Test connection with a simple client**:
   
   Using the generated xRegistry code:
   ```bash
   # Generate test producer
   xregistry generate \
     --language java \
     --style amqpproducer \
     --projectname TestProducer \
     --definitions your-definition.json \
     --output ./test-producer
   
   # Build and run tests
   cd test-producer/TestProducer
   mvn test
   ```

### Common Issues

#### Issue: Connection Refused

**Solution**: Ensure RabbitMQ is running and the plugin is enabled:
```bash
docker ps | grep rabbitmq
docker exec rabbitmq-amqp rabbitmq-plugins list | grep amqp1_0
```

#### Issue: Authentication Failed

**Solution**: Verify credentials and ensure user has permissions:
```bash
rabbitmqctl list_users
rabbitmqctl set_permissions -p / guest ".*" ".*" ".*"
```

#### Issue: Queue Not Found

**Solution**: Pre-create the queue or ensure auto-creation is enabled:
```bash
rabbitmqadmin declare queue name=myqueue durable=true auto_delete=false
```

## Performance Considerations

### Connection Pooling

For high-throughput scenarios, use connection pooling:

```java
// Java example with multiple connections
List<EventProducer> producerPool = new ArrayList<>();
for (int i = 0; i < 5; i++) {
    producerPool.add(EventProducer.createProducer(credential, options, endpoints));
}
```

### Prefetch Settings

Configure prefetch to optimize message delivery:

```java
Map<String, String> options = new HashMap<>();
options.put("node", "myqueue");
options.put("rcv-settle-mode", "first"); // Settle messages immediately
options.put("max-message-size", "1048576"); // 1MB max message size
```

## Monitoring and Management

### RabbitMQ Management UI

Access the management UI at `http://localhost:15672` (default credentials: guest/guest)

**Key metrics to monitor**:
- Connection count
- Message rates
- Queue depth
- Memory usage

### Programmatic Monitoring

Use RabbitMQ's HTTP API:

```bash
curl -u guest:guest http://localhost:15672/api/overview
```

## Security Best Practices

1. **Change default credentials**:
   ```bash
   rabbitmqctl add_user myuser mypassword
   rabbitmqctl set_permissions -p / myuser ".*" ".*" ".*"
   rabbitmqctl delete_user guest
   ```

2. **Enable TLS**:
   ```yaml
   # docker-compose.yml
   environment:
     - RABBITMQ_SSL_CERTFILE=/certs/server_cert.pem
     - RABBITMQ_SSL_KEYFILE=/certs/server_key.pem
     - RABBITMQ_SSL_CACERTFILE=/certs/ca_cert.pem
   ```

3. **Use strong authentication**:
   - Consider using client certificates
   - Integrate with LDAP or OAuth for enterprise environments

## Production Deployment

### High Availability Setup

For production, deploy RabbitMQ in a cluster.

#### RabbitMQ 4.0+ HA Cluster (Recommended)

```yaml
# docker-compose.yml for RabbitMQ 4.0+ HA cluster
version: '3.8'
services:
  rabbitmq1:
    image: rabbitmq:4-management
    hostname: rabbitmq1
    environment:
      - RABBITMQ_ERLANG_COOKIE=shared_secret_cookie
    ports:
      - "5672:5672"
      
  rabbitmq2:
    image: rabbitmq:4-management
    hostname: rabbitmq2
    environment:
      - RABBITMQ_ERLANG_COOKIE=shared_secret_cookie
    depends_on:
      - rabbitmq1
      
  rabbitmq3:
    image: rabbitmq:4-management
    hostname: rabbitmq3
    environment:
      - RABBITMQ_ERLANG_COOKIE=shared_secret_cookie
    depends_on:
      - rabbitmq1
```

#### RabbitMQ 3.x HA Cluster

```yaml
# docker-compose.yml for RabbitMQ 3.x HA cluster
version: '3.8'
services:
  rabbitmq1:
    image: rabbitmq:3-management
    hostname: rabbitmq1
    environment:
      - RABBITMQ_ERLANG_COOKIE=shared_secret_cookie
      - RABBITMQ_PLUGINS=rabbitmq_amqp1_0
    ports:
      - "5672:5672"
      
  rabbitmq2:
    image: rabbitmq:3-management
    hostname: rabbitmq2
    environment:
      - RABBITMQ_ERLANG_COOKIE=shared_secret_cookie
      - RABBITMQ_PLUGINS=rabbitmq_amqp1_0
    depends_on:
      - rabbitmq1
      
  rabbitmq3:
    image: rabbitmq:3-management
    hostname: rabbitmq3
    environment:
      - RABBITMQ_ERLANG_COOKIE=shared_secret_cookie
      - RABBITMQ_PLUGINS=rabbitmq_amqp1_0
    depends_on:
      - rabbitmq1
```

### Load Balancing

Use a load balancer (e.g., HAProxy, NGINX) to distribute connections:

```nginx
# nginx.conf
stream {
    upstream rabbitmq_amqp {
        server rabbitmq1:5672;
        server rabbitmq2:5672;
        server rabbitmq3:5672;
    }
    
    server {
        listen 5672;
        proxy_pass rabbitmq_amqp;
    }
}
```

## Migration from AMQP 0.9.1

If you're migrating from AMQP 0.9.1 to AMQP 1.0:

1. **Review routing logic**: AMQP 1.0 uses a simpler routing model
2. **Update connection code**: Use AMQP 1.0 connection strings
3. **Test thoroughly**: Verify message delivery and routing
4. **Run both protocols**: RabbitMQ can run both protocols simultaneously during migration

## Additional Resources

- [RabbitMQ AMQP 1.0 Plugin Documentation](https://www.rabbitmq.com/plugins.html)
- [AMQP 1.0 Specification](http://docs.oasis-open.org/amqp/core/v1.0/amqp-core-overview-v1.0.html)
- [xRegistry CLI Documentation](https://github.com/clemensv/xregistry-cli)
- [Apache Qpid Proton](https://qpid.apache.org/proton/) - AMQP 1.0 client library

## Support

For issues specific to:
- **RabbitMQ**: Check the [RabbitMQ mailing list](https://groups.google.com/g/rabbitmq-users)
- **xRegistry CLI**: Open an issue on [GitHub](https://github.com/clemensv/xregistry-cli/issues)
- **AMQP 1.0 Protocol**: Consult the [OASIS AMQP specification](http://docs.oasis-open.org/amqp/core/v1.0/os/amqp-core-overview-v1.0-os.html)
