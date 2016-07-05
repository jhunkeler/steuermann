# Steuermann

## How to pronounce the name:

http://www.forvo.com/word/steuer-/#de

http://www.forvo.com/word/mann/#de


## To install:

```
python setup.py install
```

Put the installed script, `steuermann_report.cgi`, on your web server.

## To configure:

```bash
# Create default configuration directory
mkdir -p ~/.steuermann/default

# Copy default hosts.ini template
cp steuermann/hosts.ini ~/.steuermann/default

# Generate basic configuration file
cat << EOF >  ~/.steuermann/default/config.py
db_creds = '/path/to/steuermann.db'
logdir = '/path/to/logs'
host_logs = '/path/to/host_logs'
EOF
```

You can override the default configuration directory by setting `STEUERMANN_CONFIG`:

```bash
export STEUERMANN_CONFIG=/alternate/path/here
```

## To run:

```
smc [ -a ] [ -r run_name ] file.sm
```

