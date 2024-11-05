To use this:

1. install `fast`: npm install --global fast-cli
2. setup a crontab:
   0 \* \* \* \* /Users/:your*username/.nodenv/shims/fast --json --single-line > ~/\_fast/speed*$(date +\%Y-\%m-\%d\_\%H:\%M).json

3. setup a webserver to serve the files:
   python3 -m http.server 7777
4. open the html file in a browser, view the graph:
   open http://localhost:7777/graph.html

Debugging:
crontab -l
crontab -e

output cron run emails and dates
awk '/^From / { print_email=0 } /^Date: / { date_line=$0; print_email=1 } print_email && !/^From / { print date_line; print; }' /var/mail/drewbarnes
