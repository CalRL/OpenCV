# If a virtual environment doesn't exist, use the following command to create it
```bash
python -m venv .venv
```

# Activate the virtual environment
## Windows
```bash
./.venv/Scripts/activate
```

## macOS / Linux:
```bash
source /.venv/Scripts/activate
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


# [Optional] Deactivate environment
```bash
deactivate
```

