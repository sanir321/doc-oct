import re
h = open("test_output.html").read()
am = re.search(r'<div class="authors">(.*?)</div>', h, re.DOTALL)
if am:
    print("AUTHORS:", am.group(1)[:400])

# Also check the analysis to see where authors come from
import json
# Read the check_ieee.html or look at what the API returns
