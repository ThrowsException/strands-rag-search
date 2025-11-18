// Using Node.js built-in WebSocket (available in Node.js 21+)

// Configuration
const CLOUDFRONT_DOMAIN = 'd28h19b8os195e.cloudfront.net';
const APPSYNC_HTTP_DOMAIN = 'hz3pcq3xebc5dpvj4kncu7dttu.appsync-api.us-east-1.amazonaws.com';
const APPSYNC_REALTIME_DOMAIN = 'hz3pcq3xebc5dpvj4kncu7dttu.appsync-realtime-api.us-east-1.amazonaws.com';
const API_KEY = process.env.APPSYNC_API_KEY || '';
const CHANNEL_NAMESPACE = 'default';
const CHANNEL = process.env.CHANNEL || 'test-channel';
const USE_CLOUDFRONT = process.env.USE_CLOUDFRONT !== 'false'; // Default to true

if (!API_KEY) {
  console.error('Error: APPSYNC_API_KEY environment variable is required');
  console.error('Retrieve it with: aws ssm get-parameter --name /appsync/chat-events/api-key --with-decryption --query Parameter.Value --output text');
  process.exit(1);
}

/**
 * AppSync Event API WebSocket Client
 * Connects to AppSync Events via CloudFront to receive real-time updates
 */
class AppSyncWebSocketClient {
  constructor(domain, appsyncHttpDomain, apiKey, channelNamespace, channel) {
    this.domain = domain;
    this.appsyncHttpDomain = appsyncHttpDomain;
    this.apiKey = apiKey;
    // Channels must be prefixed with namespace: namespace/channel
    this.channel = `${channelNamespace}/${channel}`;
    this.ws = null;
    this.connectionId = null;
  }

  /**
   * Base64URL encode the authorization header for AppSync
   */
  getBase64URLEncoded(authorization) {
    const json = JSON.stringify(authorization);
    const base64 = Buffer.from(json).toString('base64');

    // Convert to base64url format
    return base64
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');
  }

  /**
   * Connect to the AppSync WebSocket endpoint through CloudFront
   */
  async connect() {
    return new Promise((resolve, reject) => {
      const wsUrl = `wss://${this.domain}/event/realtime`;

      console.log(`Connecting to: ${wsUrl}`);
      console.log(`Channel: ${this.channel}`);

      // Prepare authorization header for AppSync
      // Important: host must be the AppSync HTTP endpoint, not CloudFront domain
      const authHeader = {
        host: this.appsyncHttpDomain,
        'x-api-key': this.apiKey,
      };

      const encodedAuthHeader = this.getBase64URLEncoded(authHeader);

      // AppSync requires two subprotocols:
      // 1. aws-appsync-event-ws
      // 2. header-{base64url-encoded-auth}
      const subprotocols = [
        'aws-appsync-event-ws',
        `header-${encodedAuthHeader}`
      ];

      console.log('Using subprotocols:', subprotocols);

      // Create WebSocket connection with required subprotocols
      this.ws = new WebSocket(wsUrl, subprotocols);

      this.ws.addEventListener('open', () => {
        console.log('✓ WebSocket connection established');

        // Send connection init message
        const initMessage = {
          type: 'connection_init',
        };

        this.ws.send(JSON.stringify(initMessage));
        console.log('→ Sent connection_init');
      });

      this.ws.addEventListener('message', (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message, resolve, reject);
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      });

      this.ws.addEventListener('error', (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      });

      this.ws.addEventListener('close', (event) => {
        console.log(`Connection closed: ${event.code} - ${event.reason}`);
      });

      // Timeout after 10 seconds if not connected
      setTimeout(() => {
        if (!this.connectionId) {
          reject(new Error('Connection timeout'));
        }
      }, 10000);
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleMessage(message, resolve, reject) {
    console.log('← Received:', JSON.stringify(message, null, 2));

    switch (message.type) {
      case 'connection_ack':
        console.log('✓ Connection acknowledged');
        this.connectionId = message.connectionTimeoutMs;

        // Subscribe to the channel
        this.subscribe();
        resolve();
        break;

      case 'subscribe_success':
        console.log(`✓ Subscribed to channel: ${this.channel} (ID: ${message.id})`);
        break;

      case 'publish_success':
        console.log(`✓ Event published successfully (ID: ${message.id})`);
        break;

      case 'data':
        console.log('\n📨 Received event data:');
        // Events are stringified, so parse them
        if (message.events) {
          message.events.forEach((event) => {
            console.log(JSON.parse(event));
          });
        }
        break;

      case 'error':
        console.error('❌ Error:', message);
        // Don't reject on error - just log it
        if (message.errors) {
          message.errors.forEach((err) => {
            console.error(`  ${err.errorType}: ${err.message}`);
          });
        }
        break;

      case 'ka':
        // Keep-alive message, ignore
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }

  /**
   * Generate a unique message ID
   */
  generateMessageId() {
    return `msg-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  }

  /**
   * Subscribe to a channel to receive events
   */
  subscribe() {
    const subscribeMessage = {
      type: 'subscribe',
      id: this.generateMessageId(),
      channel: this.channel,
      authorization: {
        'x-api-key': this.apiKey,
        host: this.appsyncHttpDomain,
      },
    };

    console.log(`→ Subscribing to channel: ${this.channel}`);
    console.log('  Subscribe message:', JSON.stringify(subscribeMessage, null, 2));
    this.ws.send(JSON.stringify(subscribeMessage));
  }

  /**
   * Publish an event to the channel
   */
  publish(event) {
    const publishMessage = {
      type: 'publish',
      id: this.generateMessageId(),
      channel: this.channel,
      events: [JSON.stringify(event)], // Events must be stringified JSON
      authorization: {
        'x-api-key': this.apiKey,
      },
    };

    this.ws.send(JSON.stringify(publishMessage));
    console.log('→ Published event:', event);
  }

  /**
   * Close the WebSocket connection
   */
  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Main execution
async function main() {
  const wsEndpoint = USE_CLOUDFRONT ? CLOUDFRONT_DOMAIN : APPSYNC_REALTIME_DOMAIN;

  console.log('AppSync WebSocket Client');
  console.log('========================================');
  console.log(`Endpoint: ${USE_CLOUDFRONT ? 'CloudFront' : 'Direct AppSync'}`);
  console.log('========================================\n');

  const client = new AppSyncWebSocketClient(
    wsEndpoint,
    APPSYNC_HTTP_DOMAIN,
    API_KEY,
    CHANNEL_NAMESPACE,
    CHANNEL
  );

  try {
    await client.connect();
    console.log('\n✓ Connected and subscribed! Listening for events...\n');
    console.log('Press Ctrl+C to exit\n');

    // Example: Publish a test event after 3 seconds
    setTimeout(() => {
      console.log('\n📤 Publishing test event...');
      client.publish({
        message: 'Hello from Node.js client!',
        timestamp: new Date().toISOString(),
      });
    }, 3000);

  } catch (error) {
    console.error('Failed to connect:', error);
    process.exit(1);
  }

  // Handle graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n\nShutting down...');
    client.close();
    process.exit(0);
  });
}

main();
