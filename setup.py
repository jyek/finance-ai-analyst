from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="finance-ai-analyst",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python package for managing financial data through Google Workspace APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/finance-ai-analyst",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Creative Commons License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyautogen>=0.2.19",
        "pandas>=1.3.0",
        "gspread>=5.12.0",
        "google-auth>=2.23.4",
        "google-auth-oauthlib>=1.1.0",
        "google-auth-httplib2>=0.1.1",
        "google-api-python-client>=2.108.0",
        "yfinance>=0.2.0",
        "matplotlib>=3.5.0",
        "numpy>=1.21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.910",
        ],
    },
    keywords="finance, google-workspace, google-sheets, google-docs, financial-analysis, ai-agent",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/finance-ai-analyst/issues",
        "Source": "https://github.com/yourusername/finance-ai-analyst",
        "Documentation": "https://github.com/yourusername/finance-ai-analyst#readme",
    },
) 