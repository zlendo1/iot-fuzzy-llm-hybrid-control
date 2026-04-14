#!/usr/bin/env python
"""Health check script for the IoT Fuzzy-LLM application container.

This script performs a meaningful health check by verifying the gRPC server
is responding on the configured port.
"""

import sys
import os

# Allow importing from the app
sys.path.insert(0, '/app')

def health_check():
    """Check if the gRPC server is healthy."""
    try:
        import grpc
        
        # Get port from environment or use default
        port = os.environ.get('IOT_GRPC_PORT', '50051')
        host = 'localhost'
        
        # Create channel
        channel = grpc.insecure_channel(f'{host}:{port}')
        
        # Wait for channel to be ready (with timeout)
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            print(f"gRPC server is healthy on {host}:{port}")
            return 0
        except grpc.FutureTimeoutError:
            print(f"gRPC server not responding on {host}:{port}")
            return 1
    except ImportError:
        print("grpc module not available")
        return 1
    except Exception as e:
        print(f"Health check failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(health_check())
