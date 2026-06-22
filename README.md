# 🚀 SpaceIntel AI

AI-Powered Space Intelligence Platform

## Overview

SpaceIntel AI is a space intelligence and news analysis platform that collects information from trusted space-related sources and transforms raw news into actionable intelligence using Artificial Intelligence.

The platform automatically gathers articles from multiple space news sources, categorizes them, and generates AI-powered summaries to help users quickly understand:

* What happened
* Why it matters
* Potential impact
* Long-term significance

The goal is to make space information more accessible, understandable, and useful for students, researchers, enthusiasts, and decision-makers.


## Problem Statement

Space-related information is scattered across multiple websites and news sources.

Users often face challenges such as:

* Information overload
* Duplicate news coverage
* Technical complexity
* Lack of concise intelligence summaries

There is a need for a system that can collect, organize, and explain space developments in a simple and actionable way.


## Solution

SpaceIntel AI provides:

* Automated RSS news aggregation
* AI-powered article analysis
* Space intelligence summaries
* Category-based filtering
* Centralized space information dashboard

Instead of reading lengthy articles, users receive concise AI-generated insights.


## Features

### News Aggregation

* Collects articles from multiple space news sources
* Synchronizes RSS feeds automatically

### AI Analysis

* Generates intelligent summaries
* Highlights key insights
* Explains importance and impact

### Category Filtering

* Astronomy
* Space Exploration
* Space Technology
* Space Business
* Research & Discoveries

### Search Functionality

* Search articles by title or keywords

### Modern Dashboard

* Clean Streamlit-based interface
* Responsive layout
* Dark-theme user experience


## Technology Stack

### Frontend

* Streamlit

### Backend

* Python

### Database

* SQLite

### AI

* Google Gemini API

### Data Sources

* NASA
* ESA
* Space.com
* SpaceNews
* RSS Feeds


## Project Structure

```text
SPACEINTELAI/

├── app.py
├── config.py
├── database.py
├── gemini_analyzer.py
├── rss_fetcher.py
├── requirements.txt
├── spaceintel_banner.png
├── .streamlit/
├── README.md
└── .gitignore
```


## Installation

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/spaceintel-ai.git
cd spaceintel-ai
```

### Create Virtual Environment

```bash
python -m venv .venv
```

### Activate Environment

Windows:

```bash
.venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```


## Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=YOUR_API_KEY
```


## Run Application

```bash
streamlit run app.py
```

Application will be available at:

```text
http://localhost:8501
```


## Future Improvements

* User authentication
* Personalized intelligence feeds
* Space mission tracking
* Satellite monitoring dashboard
* AI-powered trend prediction
* Advanced analytics
* Mobile application
* Multi-language support


## Use Cases

* Space enthusiasts
* Astronomy students
* Researchers
* Educators
* Space startups
* Industry analysts


## AI Approach

The system uses Large Language Models through the Gemini API to:

* Analyze article content
* Generate concise intelligence summaries
* Extract important information
* Provide contextual understanding

AI acts as the intelligence layer on top of collected space data.


## IBM AI Builder Challenge Alignment

This project aligns with the "Advance Space Exploration with AI" challenge by:

* Making space information more accessible
* Transforming raw space data into insights
* Using AI as a core functional component
* Supporting better decision-making through intelligent analysis


## Author

Vasu Singuri

B.Tech Artificial Intelligence & Machine Learning


## License

This project is intended for educational, research, and demonstration purposes.
