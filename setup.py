from setuptools import setup, find_packages

setup(
    name="reminder",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5",
        "schedule",
        "plyer",
    ],
    entry_points={
        'console_scripts': [
            'reminder=reminder.main:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A reminder application",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/reminder",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 