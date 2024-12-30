from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cpai",
    version="2.0.0",
    author="Sock",
    author_email="sock@hey.com",
    description="A tool to concatenate multiple files into a single markdown text string for AI assistants",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sockdrawermoney/cpai",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "pyperclip>=1.8.0",
        "pytest>=7.0.0",
        "esprima>=4.0.0",
        "tiktoken>=0.5.1",
        "pathspec>=0.11.0",
    ],
    entry_points={
        "console_scripts": [
            "cpai=cpai:main"
        ],
    },
)