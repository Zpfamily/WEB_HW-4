from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import mimetypes
from typing import Any
from urllib.parse import parse_qs
from datetime import datetime
import socket
import json
import threading
import urllib.parse
import logging

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
        size = self.headers.get("Content-Length")
        data = self.rfile.read(int(size))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, ('127.0.0.1', 5000))
        client_socket.close()
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

def save_data(data):
    try:
        data_parse = urllib.parse.unquote_plus(data.decode())
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        new_data = {current_time: {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}}

        directory_path = os.path.join(os.path.dirname(__file__), 'storage')
        file_path = os.path.join(directory_path, 'data.json')

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = {}

        existing_data.update(new_data)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=2)

    except Exception as e:
        logging.error(f"Error saving data: {e}")
    
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
            save_data(data)
    
    except KeyboardInterrupt:
        udp_server.close()

     
        
if __name__ == '__main__':
    
    http_thread = threading.Thread(target=run_server)
    udp_thread = threading.Thread(target=run_udp_server)
    http_thread.start()
    udp_thread.start()
    try:
        http_thread.join()
        udp_thread.join()
    except KeyboardInterrupt:
        print("Server terminated by user.")
