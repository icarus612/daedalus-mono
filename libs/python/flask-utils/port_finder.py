import socket
import os


def find_available_port(start_port=3000, end_port=3100):
    """
    Find an available port in the specified range.
    
    Args:
        start_port: Starting port number (default: 3000)
        end_port: Ending port number (default: 3100)
        
    Returns:
        int: Available port number
        
    Raises:
        RuntimeError: If no available port is found in the range
    """
    # Check if PORT environment variable is set
    env_port = os.environ.get('PORT')
    if env_port:
        port = int(env_port)
        if is_port_available(port):
            return port
        # If env port is not available, fall through to find another
    
    # Search for available port in range
    for port in range(start_port, end_port + 1):
        if is_port_available(port):
            return port
    
    raise RuntimeError(f"No available port found in range {start_port}-{end_port}")


def is_port_available(port):
    """
    Check if a specific port is available.
    
    Args:
        port: Port number to check
        
    Returns:
        bool: True if port is available, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(('', port))
            return True
        except socket.error:
            return False