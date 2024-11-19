from setuptools import setup, find_packages

setup(
    name="document_classifier",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "celery>=5.0.0",
        "redis>=4.0.0",
        "prometheus-client>=0.12.0",
        "structlog>=21.0.0",
        "python-magic>=0.4.24",
        "python-docx>=0.8.11",
        "openpyxl>=3.0.9",
        "pandas>=1.3.0",
        "Pillow>=8.0.0",
        "pytesseract>=0.3.8",
        "PyPDF2>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "requests>=2.0.0",
        ]
    },
)
