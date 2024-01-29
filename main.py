from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import mimetypes
from typing import Any
from urllib.parse import parse_qs
from datetime import datetime
import socket
import json
import threading

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            static_dir = os.path.join(current_dir, 'images')

            if self.path.startswith('/images/'):
                static_file_path = os.path.join(static_dir, self.path[8:])
                with open(static_file_path, 'rb') as file:
                    content = file.read()
                mt, _ = mimetypes.guess_type(static_file_path)
                self.send_response(200)
                self.send_header('Content-type', mt)
                self.end_headers()
                self.wfile.write(content)
            else:
                if self.path == '/':
                    filename = 'index.html'
                elif self.path == '/message':
                    filename = 'message.html'
                else:
                    filename = 'error.html'

                file_path = os.path.join(current_dir, filename)

                with open(file_path, 'rb') as file:
                    content = file.read()

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(content)

        except FileNotFoundError:
            filename = 'error.html'
            file_path = os.path.join(current_dir, filename)

            with open(file_path, 'rb') as file:
                content = file.read()

            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(content)
            
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            form_data = parse_qs(post_data)

            print("Received form data:",datetime.now(), form_data)

            response_text = "Form data received successfully!"
            #Temporary
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.sendto(post_data, ('127.0.0.1', 5000))
            client_socket.close()
            
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            self.wfile.write(response_text.encode('utf-8'))

        except Exception as e:
            print("Error handling POST request:", e)
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("Internal Server Error".encode('utf-8'))
            
    def do_POST_udp(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        form_data = parse_qs(post_data)
        username = form_data.get('username', [''])[0]
        message = form_data.get('message', [''])[0]

        udp_server_address = ('', 5000)
        udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = {"username": username, "message": message}
        data_string = json.dumps(data)
        udp_client.sendto(data_string.encode('utf-8'), udp_server_address)
        
    def log_message(self, format: str, *args: Any) -> None:
        pass
    
def handle_udp_data(data):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        data_dict = {timestamp: {"timestamp": timestamp}}
        
        received_data = json.loads(data.decode('utf-8'))
        for key, value in received_data.items():
            data_dict[timestamp][key] = value
            
        with open('storage/data.json', 'a') as file:
            json.dump(data_dict, file, indent=2)
            file.write('\n')

        print(f"Data received and saved: {data_dict}")

    except json.JSONDecodeError:
        print("Error decoding JSON data")
                    

def run_server():
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, MyHandler)
    print('Server is running on http://localhost:3000')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        
def run_udp_server():
    udp_server_address = ('', 5000)
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server.bind(udp_server_address)
    print('UDP Server is running on localhost:5000')

    try:
        while True:
            data, address = udp_server.recvfrom(4096)
            handle_udp_data(data)
    
    except KeyboardInterrupt:
        udp_server.close()

     
        
if __name__ == '__main__':
    
    # http_thread = threading.Thread(target=run_server)
    # http_thread.start()
    
    # run_udp_server()
    # http_thread.join()

    http_thread = threading.Thread(target=run_server)
    udp_thread = threading.Thread(target=run_udp_server)
    http_thread.start()
    udp_thread.start()
    try:
        http_thread.join()
        udp_thread.join()
    except KeyboardInterrupt:
        print("Server terminated by user.")


