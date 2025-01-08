# Variables
VENV_DIR = venv
REQ_FILE = requirements.txt
PYTHON = python3

# Default target
.PHONY: all
all: venv install

# Create virtual environment
.PHONY: venv
venv:
	@echo "Creating virtual environment..."
	@if [ ! -d $(VENV_DIR) ]; then $(PYTHON) -m venv $(VENV_DIR); fi

# Install pip requirements
.PHONY: install
install: venv
	@echo "Installing requirements..."
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r $(REQ_FILE)

# Activate virtual environment
.PHONY: activate
activate:
	@echo "Run 'source $(VENV_DIR)/bin/activate' to activate the virtual environment."

# Clean up the virtual environment
.PHONY: clean
clean:
	@echo "Removing virtual environment..."
	rm -rf $(VENV_DIR)
