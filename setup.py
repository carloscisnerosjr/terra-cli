from setuptools import setup, find_packages

setup(
    name='terra-cli',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'boto3',
        'colorama',
    ],
    entry_points={
        'console_scripts': [
            'terra=terra_cli.main:cli',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='TERRA CLI - Transform AWS Resources into Terraform with Style',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/terra-cli',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)