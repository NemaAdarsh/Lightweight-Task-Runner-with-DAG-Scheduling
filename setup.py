from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="lightweight-task-runner-with-dag-scheduling",
    version="1.0.0",
    author="Adarsh Nema",
    author_email="adarshnema6@gmail.com",
    description="A Python-based execution framework for dependent task orchestration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NemaAdarsh/lightweight-task-runner-with-dag-scheduling",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991"
        ]
    },
    entry_points={
        "console_scripts": [
            "task-runner=task_runner.cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "task_runner": ["*.json", "*.yaml", "*.yml"],
        "examples": ["*.json"],
    },
    project_urls={
        "Bug Reports": "https://github.com/NemaAdarsh/lightweight-task-runner-with-dag-scheduling/issues",
        "Source": "https://github.com/NemaAdarsh/lightweight-task-runner-with-dag-scheduling",
        "Documentation": "https://github.com/NemaAdarsh/lightweight-task-runner-with-dag-scheduling/wiki",
    },
)
