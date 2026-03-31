# HumAL Analytics

A standalone analytics tool for analyzing HumAL Active Learning sessions.

## Features

- **Web Dashboard**: Interactive Plotly Dash dashboard with multi-tab layout
- **Jupyter Notebooks**: Template notebooks for custom analysis
- **API Client**: Fetch data directly from HumAL backend
- **Comprehensive Metrics**:
  - Model performance trends (F1, accuracy, entropy)
  - Labeling efficiency (throughput, duration)
  - AL strategy effectiveness
  - Class distribution analysis
  - Session comparisons

## Installation

```bash
cd humal-analytics
pip install -e .

# With notebook support
pip install -e ".[notebooks]"
```

## Quick Start

### Web Dashboard

```bash
# Start the dashboard (connects to HumAL backend at localhost:8000)
python -m humal_analytics.dashboard

# Custom backend URL
python -m humal_analytics.dashboard --api-url http://your-backend:8000

# Custom port
python -m humal_analytics.dashboard --port 8050
```

Open http://localhost:8050 in your browser.

### Jupyter Notebooks

```bash
cd notebooks
jupyter lab
```

Available notebooks:
1. `01_session_overview.ipynb` - Load and explore session data
2. `02_labeling_analysis.ipynb` - Labeling efficiency deep-dive
3. `03_model_performance.ipynb` - Performance trends and analysis
4. `04_session_comparison.ipynb` - Compare strategies side-by-side

### Python API

```python
from humal_analytics import HumALClient, MetricsCalculator, ChartBuilder

# Connect to backend
client = HumALClient(base_url="http://localhost:8000")

# Get overview
overview = client.get_overview()
print(f"Total sessions: {overview.total_sessions}")
print(f"Best F1: {overview.best_f1_score}")

# Get session details
session = client.get_session_summary(instance_id=1)
print(f"Strategy: {session.qs_strategy}")
print(f"Latest F1: {session.latest_f1}")

# Build charts
charts = ChartBuilder(client)
fig = charts.plot_f1_trend(instance_id=1)
fig.show()
```

## Dashboard Tabs

1. **Overview**: Global statistics, strategy comparison, top performers
2. **Performance**: F1/accuracy trends, learning curves, convergence analysis
3. **Labeling**: Duration distributions, throughput metrics, bottleneck detection
4. **AL Strategy**: Uncertainty reduction, efficiency scores, budget utilization
5. **Compare**: Side-by-side session comparison with statistical analysis

## Configuration

Environment variables:
- `HUMAL_API_URL`: Backend API URL (default: `http://localhost:8000`)
- `HUMAL_ANALYTICS_PORT`: Dashboard port (default: `8050`)
- `HUMAL_ANALYTICS_DEBUG`: Enable debug mode (default: `false`)

## Architecture

```
humal-analytics/
├── humal_analytics/
│   ├── __init__.py       # Public API exports
│   ├── client.py         # HumAL API client
│   ├── models.py         # Pydantic data models
│   ├── metrics.py        # Metric calculations
│   ├── charts.py         # Plotly chart builders
│   ├── dashboard.py      # Dash app
│   └── cli.py            # CLI entry point
└── notebooks/
    └── *.ipynb           # Analysis notebooks
```

## License

MIT
