from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cpai",
    version="0.1.0",
    author="sockdrawermoney",
    author_email="sock@hey.com",
    description="Concatenate and Paste to AI - A tool for sharing code context with LLMs",
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
        "pathspec>=0.11.0"
    ],
    extras_require={
        'test': [
            'pytest>=7.0.0',
            'pytest-json-report>=1.5.0'
        ]
    },
    entry_points={
        "console_scripts": [
            "cpai=cpai.main:main"
        ],
    },
)