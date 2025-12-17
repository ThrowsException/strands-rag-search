import { Amplify } from 'aws-amplify';
import { generateClient } from 'aws-amplify/api';

Amplify.configure({
  API: {
    GraphQL: {
      endpoint: 'https://dprg1kq8103tr.cloudfront.net/graphql',
      region: 'us-east-1',
      defaultAuthMode: 'lambda',
    }
  }
});


const client = generateClient();

const query = `
  query {
    helloWorld {
      message {
        data
      }
      timestamp
    }
  }
`;

try {
  const result = await client.graphql({
    query: query,
    authToken: "foo"
  });

  console.log('Success:', result.data.helloWorld);
} catch (error) {
  console.log('Full error object:', JSON.stringify(error, null, 2));
  if (error.errors) {
    error.errors.forEach((err, i) => {
      console.log(`\nError ${i + 1}:`, err);
      if (err.extensions) {
        console.log('Extensions:', err.extensions);
      }
    });
  }
  if (error.response) {
    console.log('\nResponse status:', error.response.status);
    console.log('Response headers:', error.response.headers);
    console.log('Response body:', error.response.body);
  }
}

