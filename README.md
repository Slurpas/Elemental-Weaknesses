# Pokemon PvP Helper

A web application to quickly look up Pokemon weaknesses, resistances, and moves for PvP battles in Pokemon Go.

## Features

- **Search Pokemon**: Type any Pokemon name to get instant results
- **Type Effectiveness**: View weaknesses (2x damage), resistances (0.5x damage), and immunities (0x damage)
- **Move Information**: See common moves with their type, power, accuracy, and PP
- **Team Building**: Build and analyze teams of up to 3 Pokemon
- **Battle Simulation**: Run realistic PvP battles with customizable settings
- **Shield AI**: Multiple AI strategies for shield usage (smart, aggressive, conservative, etc.)
- **League Support**: Great League (1500 CP), Ultra League (2500 CP), Master League, and Little Cup (500 CP)
- **Real-time Analysis**: Automatic team coverage analysis and opponent matchup calculations
- **Analytics Dashboard**: Track usage statistics, popular Pokemon, and battle simulations
- **Mobile-Friendly**: Responsive design that works great on phones during battles
- **Fast Loading**: Cached data for quick access to frequently searched Pokemon

## Setup Instructions

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone or download this project** to your local machine

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open your browser** and go to:
   ```
   http://localhost:5000
   ```

## Usage

1. **Search for a Pokemon**: Type the name of any Pokemon in the search box
2. **View Results**: The app will show:
   - Pokemon sprite and basic info
   - Type weaknesses, resistances, and immunities
   - Common moves with details
3. **Switch Tabs**: Use the "Weaknesses" and "Moves" tabs to view different information

## Technical Details

- **Backend**: Python Flask web framework
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Data Source**: PokeAPI (free Pokemon database)
- **Battle Simulation Engine**: Based on PvPoke's battle algorithm and data
- **Caching**: Built-in caching to reduce API calls and improve performance

## Credits & Acknowledgments

This project uses battle simulation data and algorithms based on [PvPoke](https://pvpoke.com/), the premier Pokemon Go PvP resource. Special thanks to the PvPoke team for their excellent work in the Pokemon Go PvP community.

- **PvPoke**: Battle simulation engine and PvP rankings data
- **PokeAPI**: Pokemon species and move data

## File Structure

```
Pokemon PvP Helper/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main webpage template
└── static/
    ├── styles.css        # CSS styles
    └── script.js         # Frontend JavaScript
```

## API Endpoints

- `GET /` - Main webpage
- `GET /api/pokemon/<name>` - Get Pokemon data by name
- `GET /api/search/<query>` - Search Pokemon by partial name

## Customization

You can easily customize the app by:
- Modifying `static/styles.css` to change the appearance
- Updating `static/script.js` to add new features
- Editing `app.py` to modify the backend logic

## Troubleshooting

- **Port already in use**: Change the port in `app.py` (line with `app.run()`)
- **API errors**: The app uses the free PokeAPI, which may have rate limits
- **Slow loading**: The app caches data, so subsequent searches will be faster

## Security

This project takes security seriously. Please see [SECURITY.md](SECURITY.md) for detailed information about:

- Security measures implemented
- Known vulnerabilities
- Reporting security issues
- Security best practices

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- How to contribute
- Code style guidelines
- Testing requirements
- Pull request process

## Code of Conduct

This project adheres to a Code of Conduct. Please see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## License

This project is open source and available under the [MIT License](LICENSE).

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a complete history of changes and releases. 