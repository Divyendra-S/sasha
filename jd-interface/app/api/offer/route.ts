import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    let body;
    const contentType = request.headers.get('content-type');
    
    // Handle different content types
    if (contentType?.includes('application/json')) {
      const text = await request.text();
      if (text.trim() === '') {
        body = {};
      } else {
        try {
          body = JSON.parse(text);
        } catch (parseError) {
          console.error('JSON parse error:', parseError, 'Raw text:', text);
          return NextResponse.json(
            { error: 'Invalid JSON in request body', details: text },
            { status: 400 }
          );
        }
      }
    } else {
      // For non-JSON requests, try to get the body as text
      const text = await request.text();
      body = text ? { data: text } : {};
    }
    
    console.log('WebRTC request received:', body);
    console.log('Request type:', Object.keys(body).length === 0 ? 'Initial connection' : 'WebRTC offer');
    
    // Handle SmallWebRTC connection flow:
    // 1. Initial empty request - still forward to Python server (it may handle this)
    // 2. WebRTC offer request - forward to Python server
    console.log('Forwarding request to Python server (empty requests may be part of WebRTC flow)');
    
    // Forward exactly as received to the Python server
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    const userAgent = request.headers.get('user-agent');
    if (userAgent) {
      headers['User-Agent'] = userAgent;
    }

    console.log('Attempting to connect to Python server at http://localhost:7860/api/offer');
    
    const response = await fetch('http://localhost:7860/api/offer', {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    console.log('Python server response status:', response.status);
    console.log('Python server response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Python server error:', response.status, errorText);
      console.error('Request body that caused error:', JSON.stringify(body, null, 2));
      
      // Check if it's a 500 error with empty request (likely missing SDP/type fields)
      if (response.status === 500 && Object.keys(body).length === 0) {
        console.log('Python server rejected empty request - handling as initial connection');
        // Return a minimal successful response for initial connection attempts
        return NextResponse.json({
          message: 'Connection initialized, ready for WebRTC offer'
        });
      }
      
      // Check for other WebRTC-related errors
      if (response.status === 500 && (errorText.includes('KeyError') || errorText.includes('sdp'))) {
        console.log('Python server WebRTC error - likely missing fields');
        return NextResponse.json({
          error: 'WebRTC negotiation error',
          details: 'Missing required WebRTC fields (sdp, type)',
          requestBody: body
        }, { status: 400 });
      }
      
      // Return a more helpful error response
      return NextResponse.json(
        { 
          error: `Python server error (${response.status})`,
          details: errorText,
          requestBody: body,
          suggestion: response.status === 500 
            ? 'Python server internal error - check the Python server logs'
            : 'Make sure the Python server is configured correctly'
        },
        { status: response.status }
      );
    }

    const responseText = await response.text();
    console.log('Python server raw response:', responseText);
    
    let data;
    try {
      data = responseText ? JSON.parse(responseText) : {};
    } catch (parseError) {
      console.error('Failed to parse Python server response:', parseError);
      return NextResponse.json(
        { 
          error: 'Invalid response from Python server',
          details: responseText 
        },
        { status: 502 }
      );
    }
    
    console.log('Python server success response:', data);
    return NextResponse.json(data);
    
  } catch (error) {
    console.error('WebRTC proxy error:', error);
    
    // Check if it's a connection error
    if (error instanceof Error && (error.message.includes('fetch') || error.message.includes('ECONNREFUSED'))) {
      return NextResponse.json(
        { 
          error: 'Cannot connect to Python server',
          details: 'Connection refused - is the Python server running?',
          suggestion: 'Start the Python server with SmallWebRTC transport:\n\ncd ../server\npython3 bot.py --transport webrtc --port 7860',
          pythonServerUrl: 'http://localhost:7860'
        },
        { status: 503 }
      );
    }
    
    return NextResponse.json(
      { 
        error: 'Failed to connect to voice service',
        details: error instanceof Error ? error.message : 'Unknown error',
        suggestion: 'Check the console for more details'
      },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({ 
    status: 'Voice API endpoint active',
    pythonServerUrl: 'http://localhost:7860'
  });
}