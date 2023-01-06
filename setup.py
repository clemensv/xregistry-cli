import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="codegen",
    version="0.0.1",
    author="Your Name",
    author_email="your@email.com",
    description="A code generator for CloudEvents definitions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your/repo",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'jinja2',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'codegen=codegen.__main__:main',
        ],
    },
)
