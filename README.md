# 🏨 Hotel AI Agent

An intelligent hotel management system powered by LangChain and Claude AI.

## Features

- 🤖 Natural language interface for hotel operations
- 📅 Room availability checking
- 🎫 Automated reservation management
- 💰 Dynamic pricing based on seasons
- 🔧 Extensible tool-based architecture

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd hotel-ai-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

```bash
# Run the Streamlit app
streamlit run app/streamlit_app.py

# Or run from project root
python -m streamlit run app/streamlit_app.py
```

## Project Structure

```
hotel-ai-agent/
├── models/          # Hotel domain models (Room, Reservation, Hotel)
├── agents/          # LangChain agent and tools
├── app/             # Streamlit UI
├── config/          # Configuration and settings
├── utils/           # Helper functions
└── tests/           # Unit tests
```

## Example Queries

- "Show me available rooms for 3 guests from 15/03/2026 to 20/03/2026"
- "Book room 201 for Alice Johnson, check-in 10/03/2026, checkout 15/03/2026"
- "What's the price for a deluxe room in high season?"
- "Cancel reservation 1"

## Development

```bash
# Run tests
pytest tests/

# Format code
black .

# Type checking
mypy .
```

## License

MIT