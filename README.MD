# IoT COM6017M
This is the repository for the python side of the project.

# If a virtual environment doesn't exist, use the following command to create it
```bash
python -m venv .venv
```

# Activate the virtual environment
## Windows
```bash
.\.venv\Scripts\activate
```

## macOS / Linux:
```bash
source ./.venv/Scripts/activate
```

# Install the pip packages
```bash
pip install -r requirements.txt
```
# Verify installation
### Verify this is not empty
```bash
pip list
```
# Create environment variable file
Create an empty file called ".env"
Then, copy the keys into the file following the format.
It should look like:
```
MAIN_KEY=PROVIDEDKEY
PERFORMANCE_KEY=PROVIDEDKEY
```
Just replace "PROVIDEDKEY" with the keys provided in the report.

# Change the config IP address to reflect the one on your arduino
```yaml
#config.yaml

# Make sure these are correct!
# These will be different for you
# Plugging the arduino into the Windows machine and running the arduino IDE with the serial monitor,
# Will show you the IP that the arduino is using.
arduino:
  host: 172.20.10.2
  port: 5001
```


# [Optional] Deactivate environment
```bash
deactivate
```

