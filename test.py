
import ssl
import socket

def check_tls_support(host, port=443):
    context = ssl.create_default_context()
    
    # Specify that we want to test TLS 1.3
    context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2
    context.set_ciphers('TLS_AES_256_GCM_SHA384')
    
    try:
        with socket.create_connection((host, port)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print(f"TLS version used: {ssock.version()}")
                return True
    except Exception as e:
        print(f"Error connecting to {host}:{port} with TLS 1.3: {e}")
        return False

# Example usage, replace 'your.directus.server' with your actual Directus server host
host = 'https://hdm-dt.directus.app'
if check_tls_support(host):
    print(f"{host} supports TLS 1.3")
else:
    print(f"{host} does not support TLS 1.3 or there was an error in the connection.")