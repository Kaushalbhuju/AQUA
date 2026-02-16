import urllib.request
import urllib.error
import sys

# Redirect stdout to file
sys.stdout = open('e:/down/AQUA/error_log_utf8.txt', 'w', encoding='utf-8')

url = 'http://127.0.0.1:8000/dashboard/student_registration/'
try:
    urllib.request.urlopen(url)
    print("Request succeeded (200 OK)")
except urllib.error.HTTPError as e:
    content = e.read().decode('utf-8', errors='ignore')
    if 'Exception Value' in content:
        start = content.find('Exception Value')
        # Print a chunk around the exception value
        print(content[start:start+1000].replace('\n', ' ').replace('\r', ''))
    else:
        print("Exception Value not found in output")
        print(content[:500]) # Print start of content
except Exception as e:
    print(f"Other error: {e}")
