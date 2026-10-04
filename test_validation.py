import socket

# Test ports
s = socket.socket()
result = s.connect_ex(('127.0.0.1', 8001))
print(f'Backend port 8001: {"OPEN" if result == 0 else "CLOSED"}')
s.close()

s2 = socket.socket()
result2 = s2.connect_ex(('127.0.0.1', 5173))
print(f'Frontend port 5173: {"OPEN" if result2 == 0 else "CLOSED"}')
s2.close()