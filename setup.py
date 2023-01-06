import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cloudeventscg",
    version="0.0.1",
    author="Clemens Vasters",
    author_email="clemensv@microsoft.com",
    description="A code generator for CloudEvents definitions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clemensv/cedisco-codegen",
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
            'cloudeventscg=cloudeventscg.cloudeventscg:main',
        ],
    },
)
