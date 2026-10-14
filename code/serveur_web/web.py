import http.server
import socketserver
import threading
import webbrowser

PORT = 8080
compteur = 0

with open("squat-counter.html", "r", encoding="utf-8") as f:
    HTML = f.read()

class Handler(http.server.BaseHTTPRequestHandler):
    compteur = 0

    def do_GET(self):

        if self.path == "/squat_detecte":
            Handler.compteur += 1
            self.repondre(200, str(Handler.compteur))

        elif self.path == "/style.css":
            with open("style.css", "r", encoding="utf-8") as f:
                self.repondre(200, f.read(), "text/css; charset=utf-8")

        elif self.path == "/":
            self.repondre(200, HTML, "text/html; charset=utf-8")

        elif self.path == "/count":
            self.repondre(200, str(Handler.compteur))

        else:
            self.repondre(404, "Not found")

    def repondre(self, code, body, content_type="text/plain"):
        encoded = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        print(f"{args[0]} {args[1]}")


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serveur sur http://localhost:{PORT}")
        threading.Timer(0.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Arret.")
