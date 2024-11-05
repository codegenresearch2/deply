from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="architecture_checker",
    version="0.2.0",
    author="Your Name",
    author_email="armiworker@gmail.com",
    description="A tool to enforce architectural patterns in Django projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vashkatsi/architecture_checker",
    project_urls={
        "Bug Tracker": "https://github.com/vashkatsi/architecture_checker/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "PyYAML>=5.1",
    ],
    entry_points={
        'console_scripts': [
            'architecture_checker=architecture_checker.main:main',
        ],
    },
    include_package_data=True,
)
